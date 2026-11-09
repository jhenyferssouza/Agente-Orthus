import torch
from sentence_transformers import SentenceTransformer

def carregar_modelo_embeddings():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Carregando BGE-M3 em: {device}")
    return SentenceTransformer("BAAI/bge-m3", device=device)

def gerar_embeddings(model, texts: list):
    device = str(model.device)
    return model.encode(
        texts,
        batch_size=64 if "cuda" in device else 16,
        normalize_embeddings=True,
        show_progress_bar=True
    )