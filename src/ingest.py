import os
import logging
from pathlib import Path

import coloredlogs
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

# Configuração do log
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')

load_dotenv()


def verify_env():
    """Verifica se todas as variáveis de ambiente necessárias estão configuradas."""
    required_vars = (
        "OPENAI_API_KEY",
        "PGVECTOR_URL",
        "PGVECTOR_COLLECTION",
        "OPENAI_EMBEDDING_MODEL",
        "PDF_PATH"
    )
    for var in required_vars:
        if not os.getenv(var):
            raise RuntimeError(f"Variável de ambiente {var} não está configurada")
    logger.info("Variáveis de ambiente carregadas com sucesso.")


def split_documents(pages):
    """Divide documentos em chunks menores."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=False,
    )
    chunks = text_splitter.split_documents(pages)
    logger.info(f"Total de chunks gerados: {len(chunks)}")
    return chunks


def ingest_pdf():
    """Carrega PDF, gera embeddings e armazena no PostgreSQL."""
    verify_env()

    # 1. Carrega o PDF
    pdf_path = os.getenv("PDF_PATH")
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    if not pages:
        logger.warning("Nenhum conteúdo encontrado no PDF.")
        return

    # 2. Divide em chunks
    docs = split_documents(pages)

    # 3. Cria embeddings
    embeddings = OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )

    # 4. Conecta ao PostgreSQL e salva vetores
    connection_string = os.getenv("PGVECTOR_URL")
    collection_name = os.getenv("PGVECTOR_COLLECTION")

    try:
        store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=connection_string,
            use_jsonb=True,
        )

        ids = [f"doc-{i}" for i in range(len(docs))]
        store.add_documents(documents=docs, ids=ids)

        logger.info(f"✅ Ingestão concluída! {len(docs)} chunks salvos com sucesso.")

    except Exception as e:
        logger.error(f"❌ Erro ao salvar vetores no PostgreSQL: {e}")
        raise


if __name__ == "__main__":
    ingest_pdf()