import os
import platform
import subprocess
from dotenv import load_dotenv

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
        import tkinter as tk
        from tkinter import filedialog

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


def ingest_pdf():
    """Ponto de entrada para processar o arquivo PDF.

    Atualmente esta função apenas resolve e imprime o caminho do PDF. Substitua o
    print pela lógica real de ingestão conforme necessário.
    """
    pdf_path = resolve_pdf_path(PDF_PATH)
    if not pdf_path:
        print("Nenhum arquivo PDF foi informado ou encontrado.")
        return

    print(f"PDF selecionado: {pdf_path}")
    # TODO: Adicione aqui a lógica de ingestão do PDF usando `pdf_path`.


if __name__ == "__main__":
    ingest_pdf()