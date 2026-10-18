import os
from dotenv import load_dotenv

# LangChain: cada peça faz uma etapa do pipeline de ingestão
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

load_dotenv()

# Configurações lidas do .env
PDF_PATH = os.getenv("PDF_PATH")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
DATABASE_URL = os.getenv("DATABASE_URL")
COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")

# Regras fixadas pelo desafio
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def ingest_pdf():
    # 1) Carregar o PDF: cada página vira um "Documento" com o texto da página
    print(f"Carregando PDF: {PDF_PATH}")
    loader = PyPDFLoader(PDF_PATH)
    pages = loader.load()
    print(f"  -> {len(pages)} páginas carregadas")

    # 2) Dividir em chunks de 1000 caracteres, com 150 de sobreposição.
    #    O overlap evita cortar uma informação no meio entre dois chunks.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(pages)
    print(f"  -> {len(chunks)} chunks gerados (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    # 3) Vetorizar: cada chunk será convertido em embedding (1536 números)
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)

    # 4) Salvar no Postgres + pgVector.
    #    Na primeira execução o PGVector cria a tabela já com a dimensão do modelo.
    print("Salvando vetores no Postgres...")
    store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=DATABASE_URL,
    )

    # Apaga a collection anterior (se existir) para não duplicar chunks
    # ao rodar o ingest mais de uma vez. Como o construtor acima já cria
    # a collection, precisamos recriá-la logo após o delete.
    store.delete_collection()
    store.create_collection()

    store.add_documents(chunks)

    print(f"Ingestão concluída! Collection '{COLLECTION_NAME}' populada com {len(chunks)} vetores.")


if __name__ == "__main__":
    ingest_pdf()
