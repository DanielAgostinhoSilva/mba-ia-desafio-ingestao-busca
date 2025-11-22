# Desafio MBA Engenharia de Software com IA - Full Cycle

## Como executar

- Iniciar serviços em sequência (Ollama -> Postgres -> baixar modelo Llama3):
  - make start

- Iniciar apenas o serviço do Ollama:
  - make ai-start

- Iniciar apenas o serviço do PostgreSQL:
  - make pg-start

- Parar todos os serviços do docker-compose:
  - make ai-stop

- Limpar tudo (containers + volumes + órfãos):
  - make ai-clean

- Ver logs dos serviços:
  - make ai-logs

- Baixar o modelo Llama 3 no Ollama (exemplo):
  - make llama3

## Ingestão de PDF (src/ingest.py)
- O caminho do PDF pode ser definido via variável de ambiente `PDF_PATH`.
- Se `PDF_PATH` estiver ausente ou inválido, o script tentará abrir um seletor de arquivos:
  - No macOS: usa um diálogo nativo via AppleScript (osascript), evitando problemas de compatibilidade do tkinter que podem causar erros do tipo "macOS 26 (2601) or later required".
  - Em outros sistemas: usa `tkinter.filedialog`.
- Se a seleção gráfica não estiver disponível (ex.: ambiente headless) ou for cancelada, o script pede o caminho via terminal (CLI).

Fluxo de ingestão (LangChain + pgVector):
- O PDF é dividido em chunks de 1000 caracteres com overlap de 150.
- Cada chunk é convertido em embedding via Ollama (modelo configurável, padrão `nomic-embed-text`).
- Os vetores são armazenados no PostgreSQL usando pgVector.

Variáveis de ambiente relevantes (com padrões):
- PDF_PATH: caminho do PDF (opcional).
- OLLAMA_BASE_URL: URL do Ollama (padrão `http://localhost:11434`).
- EMBEDDINGS_MODEL: modelo de embedding do Ollama (padrão `nomic-embed-text`).
  - Se o modelo não estiver disponível localmente no Ollama, o script tentará baixá-lo automaticamente (equivalente a `ollama pull <modelo>`). Isso pode demorar e requer conexão com a internet.
- PGHOST, PGPORT, PGUSER/POSTGRES_USER, PGPASSWORD/POSTGRES_PASSWORD, PGDATABASE/POSTGRES_DB: conexão com o PostgreSQL (padrões batem com o docker-compose).
- PGVECTOR_COLLECTION: nome da coleção no pgvector (padrão `pdf_<nome-do-arquivo>`). Se já existir, será recriada (pre_delete_collection=true).

Como executar manualmente:
```
python src/ingest.py
```

Pré‑requisitos:
- Containers do `docker-compose` ativos: `make start` (sobe Ollama e PostgreSQL com pgvector).

## Conexão com o PostgreSQL (padrão)
- Host: localhost
- Porta: 5432
- Database: app
- User: postgres
- Password: postgres