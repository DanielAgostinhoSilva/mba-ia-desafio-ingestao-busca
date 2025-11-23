# Desafio MBA Engenharia de Software com IA - FullCycle

Este projeto implementa um fluxo simples de RAG (Retrieval-Augmented Generation) para:
- Ingerir um documento PDF e gerar embeddings com OpenAI
- Armazenar os vetores no Postgres + pgvector
- Consultar via CLI (chat) usando contexto recuperado do banco vetorial

Abaixo você encontra instruções para iniciar o projeto, ingerir dados e interagir com o chat, além de uma documentação resumida da arquitetura.

## 1) Pré‑requisitos
- Docker e Docker Compose instalados
- Python 3.9+ instalado (para executar os scripts localmente)
- Uma chave de API válida da OpenAI (OPENAI_API_KEY)

## 2) Configuração do ambiente
1. Copie o arquivo de exemplo de variáveis de ambiente e preencha os valores:
   
   cp .env.example .env

2. Edite o arquivo .env e informe:
   - OPENAI_API_KEY: sua chave da OpenAI
   - OPENAI_EMBEDDING_MODEL: ex.: text-embedding-3-small
   - OPENAI_LLM_MODEL: ex.: gpt-4o-mini ou gpt-4o
   - PGVECTOR_URL: URL de conexão do Postgres com pgvector (ex.: postgresql+psycopg://user:pass@localhost:5432/db)
   - PGVECTOR_COLLECTION: nome da coleção (tabela lógica) para os vetores (ex.: documentos)
   - PDF_PATH: caminho do PDF a ser ingerido (ex.: ./document.pdf)

Observação: valores padrão e validações estão implementados nos scripts em `src/`.

## 3) Subir os serviços com Docker
Você pode usar o Makefile (recomendado):

- Subir:
  make start

- Parar:
  make clean

- Parar e remover volumes (reset total):
  make remove-all

Alternativamente, diretamente com Docker Compose:

- docker compose up -d
- docker compose down

## 4) Instalar dependências Python (opcional, para rodar scripts fora do container)
Crie e ative um ambiente virtual e instale as dependências:

- python -m venv .venv
- source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
- pip install -r requirements.txt

## 5) Ingerir o PDF
Com o Postgres/pgvector em execução (via Docker), execute o script de ingestão:

- python src/ingest.py

O script:
- Valida variáveis de ambiente
- Carrega o PDF definido em `PDF_PATH`
- Divide o conteúdo em chunks
- Gera embeddings com `OPENAI_EMBEDDING_MODEL`
- Salva no banco vetorial (PGVector)

Logs de progresso são exibidos no terminal. Em caso de erro, confira a seção de Troubleshooting.

## 6) Interagir com o Chat (CLI)
Após a ingestão, rode o chat:

- python src/chat.py

Instruções na tela:
- Digite sua pergunta e pressione Enter
- Comandos para sair: sair, exit, quit ou q

A resposta é gerada por um LLM definido em `OPENAI_LLM_MODEL`, usando apenas o contexto recuperado do banco vetorial.

## 7) Variáveis de ambiente (resumo)
Os scripts validam a presença destas chaves:
- OPENAI_API_KEY
- PGVECTOR_URL
- PGVECTOR_COLLECTION
- OPENAI_EMBEDDING_MODEL (ex.: text-embedding-3-small)
- OPENAI_LLM_MODEL (ex.: gpt-4o-mini)
- PDF_PATH (caminho do PDF a processar)

Se alguma estiver ausente, o programa retornará uma mensagem de erro clara.

## 8) Documentação resumida da arquitetura
- Ingestão (`src/ingest.py`)
  - Carrega PDF (`PDF_PATH`) com PyPDFLoader
  - Fragmenta em chunks (RecursiveCharacterTextSplitter)
  - Gera embeddings (OpenAIEmbeddings)
  - Persiste vetores no Postgres via `langchain-postgres`/PGVector

- Busca e Geração (`src/search.py`)
  - Recupera documentos similares via similaridade
  - Monta um contexto textual
  - Chama `ChatOpenAI` com um prompt que restringe a resposta ao contexto

- Interface de Chat (`src/chat.py`)
  - CLI simples que lê perguntas, chama `search_prompt` e imprime a resposta

- Orquestração
  - `docker-compose.yml`: provisiona infraestrutura (ex.: Postgres/pgvector)
  - `Makefile`: atalhos para subir/derrubar serviços

## 9) Dicas de Troubleshooting
- Conexão ao banco vetorial
  - Verifique `PGVECTOR_URL` e se o container do Postgres está em execução
- Erros de autenticação OpenAI
  - Confirme `OPENAI_API_KEY` e modelos configurados
- PDF não encontrado ou vazio
  - Confira `PDF_PATH` e se o arquivo existe e tem conteúdo
- Dependências Python
  - Rode `pip install -r requirements.txt` e confirme a versão do Python

## 10) Estrutura do projeto (resumo)
- src/ingest.py — pipeline de ingestão
- src/search.py — busca e geração de resposta
- src/chat.py — CLI de interação
- docker-compose.yml — infraestrutura de suporte
- requirements.txt — dependências Python
- Makefile — comandos utilitários
- document.pdf — exemplo de PDF (ajuste `PDF_PATH` se desejar outro)

---

Pronto! Com essas etapas você consegue iniciar os serviços, ingerir o PDF e conversar com o assistente usando o conteúdo do documento como base.