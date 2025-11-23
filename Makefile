# Makefile para projeto de IA com LangChain + Docker Compose
.PHONY: start clean


start:
	 docker compose up -d

clean:
	docker compose down

remove-all:
	docker compose down -v --remove-orphans
