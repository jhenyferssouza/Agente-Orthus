import hashlib
import chromadb

def guardar_no_chromadb(pasta_chroma: str, chunks: list, embeddings):
    client = chromadb.PersistentClient(path=pasta_chroma)
    collection = client.get_or_create_collection(name="base_conhecimento")

    texts = [chunk.page_content for chunk in chunks]
    ids = []

    for chunk in chunks:
        source = chunk.metadata.get("source", "")
        page = chunk.metadata.get("page", 0)
        unique_string = f"{source}_{page}_{chunk.page_content}"
        chunk_id = hashlib.md5(unique_string.encode("utf-8")).hexdigest()
        ids.append(chunk_id)

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=[chunk.metadata for chunk in chunks]
    )
    print(f"Total de registos na coleção: {collection.count()}")
    return collection