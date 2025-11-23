import os
import logging

from pathlib import Path

import coloredlogs
from dotenv import load_dotenv
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector
import psycopg  # psycopg v3

# Configuração básica do log
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')  # já aplica cores automaticamente

load_dotenv()

def ingest_pdf():
    verify_env()

    # 1) Carrega páginas do PDF
    loader = PyPDFLoader(os.getenv("PDF_PATH"))
    pages = loader.load()
    if not pages:
        logging.warning("Nenhum conteúdo encontrado no PDF.")
        raise SystemExit(0)

    # 2) Split em chunks e remove metadados vazios
    docs = split_documents(pages)
    enriched = [
        Document(
            page_content=d.page_content,
            metadata={k: v for k, v in d.metadata.items() if v not in ("", None)}
        )
        for d in docs
    ]

    # 3) Embeddings com Openai
    embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))

    # 4) Conexão ao Postgres/pgvector
    conn_str_raw = os.getenv("PGVECTOR_URL")
    conn_sqlalchemy = _normalize_sqlalchemy_url(conn_str_raw)
    conn_psycopg = _to_psycopg_conninfo(conn_sqlalchemy)

    # Garante extensão pgvector (melhor esforço; não falha a ingestão caso indisponível)
    _ensure_pgvector_extension(conn_psycopg)

    # 5) Persiste vetores
    try:
        store = PGVector(
            embeddings=embeddings,
            collection_name=os.getenv("PGVECTOR_COLLECTION"),
            connection=conn_sqlalchemy,
            use_jsonb=True,
        )

        ids = [f"doc-{i}" for i in range(len(enriched))]
        store.add_documents(documents=enriched, ids=ids)
        logging.info("Vetores salvos com sucesso.")
    except Exception as e:
        raise RuntimeError(f"Erro ao salvar vetores no PostgreSQL: {e}")

    logger.info("Ingestão concluída com sucesso.")

def _normalize_sqlalchemy_url(url: Optional[str]) -> str:
    """
    - Se host.docker.internal estiver presente (comum quando rodando o app no host
      e o Postgres no Docker no mesmo Mac/Windows), troca por localhost para
      evitar erro de resolução de nome.
    - Garante que a URL esteja no formato SQLAlchemy (postgresql+psycopg://...)
      mas não força mudanças além do host quando não necessário.
    """
    if not url:
        return ""
    normalized = url.replace("host.docker.internal", "localhost")
    return normalized


def _to_psycopg_conninfo(sqlalchemy_url: str) -> str:
    """
    Converte uma URL SQLAlchemy (por ex. postgresql+psycopg://user:pass@host:5432/db)
    em um conninfo compatível com psycopg v3 (postgresql://user:pass@host:5432/db).
    """
    if not sqlalchemy_url:
        return ""
    if sqlalchemy_url.startswith("postgresql+psycopg://"):
        return "postgresql://" + sqlalchemy_url[len("postgresql+psycopg://"):]
    return sqlalchemy_url


def _ensure_pgvector_extension(conninfo: str) -> None:
    try:
        if not conninfo:
            raise ValueError("connection info vazio")
        with psycopg.connect(conninfo) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    except Exception as e:
        print(f"Aviso: não foi possível garantir a extensão pgvector: {e}")

def split_documents(pages: list[Document]) -> list[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=False,
    ).split_documents(pages)
    logger.info("Total de chunks gerados: %d", len(text_splitter))
    return text_splitter


def verify_env():
    for k in ("OPENAI_API_KEY", "PGVECTOR_URL", "PGVECTOR_COLLECTION", "OPENAI_EMBEDDING_MODEL", "PDF_PATH"):
        if not os.getenv(k):
            raise RuntimeError(f"Environment variable {k} is not set")
    logging.info("Variaveis de ambiente carregadas com sucesso.")




if __name__ == "__main__":
    ingest_pdf()