from search import search_prompt

def main():
    print("Chat iniciado! Faça sua pergunta sobre o documento (ou digite 'sair' para encerrar).\n")
    chain = search_prompt()

    if not chain:
        print("Não foi possível iniciar o chat. Verifique os erros de inicialização.")
        return

    while True:
        try:
            pergunta = input("PERGUNTA: ").strip()
        except (EOFError, KeyboardInterrupt):
            # Ctrl+C ou Ctrl+D encerra o chat de forma limpa
            print("\nAté logo!")
            break

        if not pergunta:
            continue

        if pergunta.lower() in ("sair", "exit", "quit"):
            print("Até logo!")
            break

        try:
            resposta = chain(pergunta)
            print(f"RESPOSTA: {resposta}\n")
        except Exception as e:
            print(f"ERRO ao gerar resposta: {e}\n")

if __name__ == "__main__":
    main()