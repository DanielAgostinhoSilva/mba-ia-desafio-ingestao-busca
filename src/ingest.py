import os
import platform
import subprocess
from dotenv import load_dotenv
import ollama
import psycopg2

# Importações de terceiros utilizadas no fluxo principal
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama.embeddings import OllamaEmbeddings
try:
    from langchain_community.vectorstores.pgvector import PGVector
except Exception as _pgv_err:
    PGVector = None  # type: ignore
    _PGV_IMPORT_ERROR = _pgv_err
else:
    _PGV_IMPORT_ERROR = None

# Importações condicionais para GUI (evitar problemas no macOS)
if platform.system() != "Darwin":
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        tk = None
        filedialog = None
else:
    tk = None
    filedialog = None

# Carrega variáveis de ambiente de um arquivo .env, se presente
load_dotenv()

PDF_PATH = os.getenv("PDF_PATH")


def _select_pdf_with_gui() -> "Optional[str]":
    """Tenta abrir um seletor de arquivos nativo para escolher um PDF.
    Retorna o caminho selecionado ou None se o usuário cancelar ou se a GUI não estiver disponível.
    No macOS utiliza AppleScript para evitar travamentos do tkinter em alguns sistemas.
    """
    try:
        # Prefira o diálogo nativo via AppleScript no macOS para evitar problemas de dependência do Tk
        if platform.system() == "Darwin":
            script = (
                'set theFile to POSIX path of (choose file of type {"com.adobe.pdf"} ' 
                'with prompt "Selecione o arquivo PDF")\nreturn theFile'
            )
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                path = (result.stdout or "").strip()
                return path or None
            # Provavelmente o usuário cancelou
            return None

        # Recurso ao tkinter em plataformas não macOS
        if tk is None or filedialog is None:
            return None

        root = tk.Tk()
        root.withdraw()  # Oculta a janela principal
        root.update()
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo PDF",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        # Destroi o root para fechar corretamente o Tk
        root.destroy()
        return file_path or None
    except Exception:
        # Em ambientes sem interface gráfica (headless) ou sem Tk disponível, voltar silenciosamente
        return None


def _select_pdf_fallback_cli() -> "Optional[str]":
    """Recurso ao terminal (CLI) quando a interface gráfica não estiver disponível.
    Retorna o caminho informado se fornecido e existir; caso contrário, None.
    """
    try:
        user_input = input("Informe o caminho do arquivo PDF: ").strip()
    except EOFError:
        return None
    return user_input or None


def resolve_pdf_path(initial_path: "Optional[str]") -> "Optional[str]":
    """Resolve um caminho válido para o PDF.

    Ordem:
    1) Usa initial_path se fornecido e se o arquivo existir.
    2) Abre um seletor de arquivos (GUI) para o usuário escolher um PDF.
    3) Recorre ao prompt no terminal (CLI) se a GUI não estiver disponível.

    Retorna um caminho válido ou None se nada for selecionado/fornecido.
    """
    # 1) Caminho definido por variável de ambiente
    if initial_path and os.path.isfile(initial_path):
        return initial_path

    # 2) Seleção via interface gráfica (GUI)
    selected = _select_pdf_with_gui()
    if selected and os.path.isfile(selected):
        return selected

    # 3) Recurso ao CLI
    typed = _select_pdf_fallback_cli()
    if typed and os.path.isfile(typed):
        return typed

    return None


def _env(name: str, default: str) -> str:
    """Obtém variável de ambiente com padrão."""
    val = os.getenv(name)
    return val if val not in (None, "") else default


def _ensure_pgvector_extension(conn_str: str) -> None:
    try:
        conn = psycopg2.connect(conn_str)  # type: ignore
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Aviso: não foi possível garantir a extensão pgvector: {e}")


def ingest_pdf():
    """Ponto de entrada para processar o arquivo PDF.

    Fluxo de ingestão:
    - Carrega o PDF.
    - Divide em chunks de 1000 caracteres com overlap de 150.
    - Gera embeddings de cada chunk via LangChain.
    - Armazena os vetores no PostgreSQL com pgVector.
    """
    pdf_path = resolve_pdf_path(PDF_PATH)
    if not pdf_path:
        print("Nenhum arquivo PDF foi informado ou encontrado.")
        return

    print(f"PDF selecionado: {pdf_path}")

    # Importações já estão no topo do arquivo (LangChain, PGVector, etc.)

    # 1) Carrega páginas do PDF
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    if not pages:
        print("Nenhum conteúdo encontrado no PDF.")
        return

    # 2) Split em chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = splitter.split_documents(pages)
    print(f"Total de chunks gerados: {len(docs)}")

    # 3) Embeddings com Ollama (modelo configurável)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # 4) Conexão ao Postgres/pgvector
    pg_user = _env("PGUSER", _env("POSTGRES_USER", "postgres"))
    pg_pass = _env("PGPASSWORD", _env("POSTGRES_PASSWORD", "postgres"))
    pg_host = _env("PGHOST", "localhost")
    pg_port = _env("PGPORT", "5432")
    pg_db = _env("PGDATABASE", _env("POSTGRES_DB", "app"))
    conn_str = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

    # Garante extensão pgvector
    _ensure_pgvector_extension(conn_str)

    # Coleção baseada no nome do arquivo
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    collection = _env("PGVECTOR_COLLECTION", f"pdf_{base_name}")

    # 5) Persiste vetores; pre_delete_collection=True para reprocessamentos
    print(f"Gravando vetores na coleção: {collection}")

    try:
        _ = PGVector.from_documents(
            documents=docs,
            embedding=embeddings,
            collection_name=collection,
            connection_string=conn_str,
            use_jsonb=True,
            pre_delete_collection=True,
        )
    except Exception as e:
        print(f"Erro ao salvar vetores no PostgreSQL: {e}")
        return

    print("Ingestão concluída com sucesso.")


if __name__ == "__main__":
    ingest_pdf()