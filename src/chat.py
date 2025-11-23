from search import search_prompt


def main():
    print("CLI de Chat (RAG) — digite sua pergunta. Digite 'sair' para encerrar.")
    try:
        while True:
            try:
                question = input("Você: ").strip()
            except EOFError:
                print("\nEncerrando.")
                break

            if question.lower() in {"sair", "exit", "quit", "q"}:
                print("Até mais!")
                break

            if not question:
                continue

            response = search_prompt(question)
            if response is None:
                # search_prompt retorna None apenas se a pergunta for vazia; já tratado acima.
                continue

            print(f"Assistente: {response}\n")
    except KeyboardInterrupt:
        print("\nEncerrando.")


if __name__ == "__main__":
    main()