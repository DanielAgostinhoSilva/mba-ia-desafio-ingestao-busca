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

Como executar manualmente:
```
python src/ingest.py
```

## Conexão com o PostgreSQL (padrão)
- Host: localhost
- Porta: 5432
- Database: app
- User: postgres
- Password: postgres