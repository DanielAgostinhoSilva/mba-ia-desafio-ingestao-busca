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

## Conexão com o PostgreSQL (padrão)
- Host: localhost
- Porta: 5432
- Database: app
- User: postgres
- Password: postgres