import os
import chromadb
from src.embeddings import carregar_modelo_embeddings
from src.reranker import Reranker

BASE_DIR = "./Base_conhecimento"
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

def pesquisar_com_rerank():
    # 1. Conectar ao ChromaDB e carregar modelos
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name="base_conhecimento")
    
    embedding_model = carregar_modelo_embeddings()
    reranker = Reranker(model_name="BAAI/bge-reranker-base") # Ou bge-reranker-large

    pergunta = input("\nDigite uma pergunta: ")
    query_vec = embedding_model.encode([pergunta], normalize_embeddings=True)

    # 2. Busca inicial no ChromaDB com janela MAIOR (top 20)
    resultados_iniciais = collection.query(
        query_embeddings=query_vec.tolist(),
        n_results=20
    )

    docs_candidatos = resultados_iniciais["documents"][0]
    meta_candidatos = resultados_iniciais["metadatas"][0]

    # 3. Aplicar o Reranking para filtrar os TOP 5 melhores
    resultados_finais = reranker.rerank(
        query=pergunta,
        documents=docs_candidatos,
        metadatas=meta_candidatos,
        top_k=5
    )

    # 4. Exibir resultados reordenados
    print("\n--- RESULTADOS FINAIS APÓS RERANKING ---")
    for i, res in enumerate(resultados_finais):
        print(f"\n[Posição {i+1}] (Score: {res['score']:.4f})")
        print(f"Fonte: {res['metadata'].get('source', 'N/A')} | Página: {res['metadata'].get('page', 'N/A')}")
        print(f"Trecho: {res['document'][:250]}...")

if __name__ == "__main__":
    pesquisar_com_rerank()