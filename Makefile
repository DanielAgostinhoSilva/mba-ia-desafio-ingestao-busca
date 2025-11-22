# Makefile para projeto de IA com LangChain + Docker Compose
.PHONY: ai-start ai-stop ai-clean ai-logs pg-start start

# inicia todos os serviços em sequência: Ollama -> Postgres -> baixar modelo Llama3
start:
	 $(MAKE) ai-start
	 $(MAKE) pg-start
	 $(MAKE) nomic-embed-text

clean:
	docker compose down -v --remove-orphans

# inicia o servico do ollama
ai-start:
	 docker compose up -d ollama

# para o servico do ollama
ai-stop:
	 docker compose stop ollama

# remove o servico do ollama
ai-clean:
	 docker compose down ollama -v --remove-orphans

# visualiza o log do servico ollama
ai-logs:
	 docker compose logs -f ollama

# Iniciar somente o serviço do PostgreSQL
pg-start:
	 docker compose up -d postgres

# para o servico do postgres
pg-stop:
	docker compose stop postgres

# remove o servico do postgres (containers, volumes e órfãos)
pg-clean:
	 docker compose down postgres -v --remove-orphans

# visualiza os logs do servico do postgres
pg-logs:
	 docker compose logs -f postgres

# baixa o modelo llama3 no ollama via API
llama3:
	curl -N -H "Content-Type: application/json" http://localhost:11434/api/pull -d '{"name":"llama3"}'

# baixa o modelo nomic-embed-text no ollama via API
nomic-embed-text:
	curl -N -H "Content-Type: application/json" http://localhost:11434/api/pull -d '{"name":"nomic-embed-text"}'