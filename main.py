import os
from src.loader import carregar_e_dividir_documentos
from src.embeddings import carregar_modelo_embeddings, gerar_embeddings
from src.database import guardar_no_chromadb

BASE_DIR = "./base_conhecimento"
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documentos")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

def executar_pipeline():
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    os.makedirs(CHROMA_DIR, exist_ok=True)

    # 1. Chunking
    chunks = carregar_e_dividir_documentos(DOCUMENTS_DIR)
    if not chunks:
        print("Nenhum documento encontrado.")
        return

    # 2. Embeddings
    model = carregar_modelo_embeddings()
    texts = [chunk.page_content for chunk in chunks]
    embeddings = gerar_embeddings(model, texts)

    # 3. Armazenamento
    guardar_no_chromadb(CHROMA_DIR, chunks, embeddings)
    print("Pipeline de ingestão concluído com sucesso!")

if __name__ == "__main__":
    executar_pipeline()