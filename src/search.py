import os

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector


load_dotenv()

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def search_prompt(question=None):
    """Busca documentos similares e gera resposta usando LLM."""

    # Valida entrada
    if not question or not question.strip():
        return None

    # Verifica variáveis de ambiente
    required_vars = [
        "OPENAI_API_KEY",
        "PGVECTOR_URL",
        "PGVECTOR_COLLECTION",
        "OPENAI_EMBEDDING_MODEL",
        "OPENAI_LLM_MODEL"
    ]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        error_msg = f"Variáveis de ambiente ausentes: {', '.join(missing)}"
        raise RuntimeError(error_msg)

    # Configura embeddings e conexão
    embeddings = OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )

    store = PGVector(
        embeddings=embeddings,
        collection_name=os.getenv("PGVECTOR_COLLECTION"),
        connection=os.getenv("PGVECTOR_URL"),
        use_jsonb=True,
    )

    # Busca documentos similares
    try:
        docs = store.similarity_search(question, k=10)
    except Exception as e:
        return f"Erro ao consultar o banco vetorial: {e}"

    if not docs:
        return "Não tenho informações necessárias para responder sua pergunta."

    # Monta o contexto
    contexto_partes = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        page = meta.get("page")
        source = meta.get("source", "")

        header = f"[Trecho {i}"
        if page is not None:
            header += f" - página {page}"
        if source:
            header += f" - {source}"
        header += "]"

        contexto_partes.append(f"{header}\n{doc.page_content}")

    contexto = "\n\n---\n\n".join(contexto_partes)

    # Gera resposta com LLM
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=question)

    try:
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_LLM_MODEL"),
            temperature=0.5
        )
        response = llm.invoke(prompt)

        # Extrai conteúdo da resposta
        answer = response.content if hasattr(response, "content") else str(response)
        return answer

    except Exception as e:
        return f"Erro ao gerar resposta: {e}"