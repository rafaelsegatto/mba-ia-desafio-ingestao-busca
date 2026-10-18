import os
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_postgres import PGVector

load_dotenv()

# Configurações lidas do .env (mesmas do ingest!)
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL")
DATABASE_URL = os.getenv("DATABASE_URL")
COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")

# O desafio fixa k=10: buscamos os 10 chunks mais parecidos com a pergunta
K_RESULTS = 10

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def get_vector_store():
    """Reconecta ao Postgres com os MESMOS parâmetros do ingest.
    É obrigatório usar o mesmo modelo de embeddings e a mesma collection,
    senão a busca não encontra nada."""
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
    return PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=DATABASE_URL,
    )


def search_context(store, question):
    """Busca os k chunks mais similares à pergunta e concatena os textos."""
    results = store.similarity_search_with_score(question, k=K_RESULTS)
    # results é uma lista de tuplas (Document, score); o menor score = mais similar
    return "\n\n".join(doc.page_content for doc, _score in results)


def answer_question(store, llm, question):
    """Executa o fluxo completo: busca -> monta prompt -> chama a LLM."""
    contexto = search_context(store, question)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=question)
    response = llm.invoke(prompt)
    return response.content


def search_prompt(question=None):
    """Sem argumento: devolve a função "ask" para o chat.py usar.
    Com argumento: responde a pergunta imediatamente."""
    store = get_vector_store()
    llm = ChatOpenAI(model=OPENAI_CHAT_MODEL)

    def ask(pergunta):
        return answer_question(store, llm, pergunta)

    if question:
        return ask(question)
    return ask


if __name__ == "__main__":
    # Teste rápido direto: python src/search.py "sua pergunta aqui"
    import sys

    pergunta = " ".join(sys.argv[1:]) or "Qual o faturamento da empresa?"
    print(search_prompt(pergunta))
