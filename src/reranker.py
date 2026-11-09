import torch
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-large"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Carregando modelo de Reranking ({model_name}) em: {device}")
        # BAAI/bge-reranker-large ou BAAI/bge-reranker-base
        self.model = CrossEncoder(model_name, device=device)

    def rerank(self, query: str, documents: list[str], metadatas: list[dict], top_k: int = 5):
        if not documents:
            return []

        # Criar os pares (pergunta, documento) para avaliação do Cross-Encoder
        pairs = [[query, doc] for doc in documents]
        
        # Calcular os scores de relevância
        scores = self.model.predict(pairs)

        # Combinar documentos, metadados e pontuações
        results = [
            {"document": doc, "metadata": meta, "score": float(score)}
            for doc, meta, score in zip(documents, metadatas, scores)
        ]

        # Ordenar decrescente pelo score e retornar os top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]