import os
import pymupdf  # Substituto atualizado do fitz
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

def pdf_para_markdown(caminho_pdf: str) -> str:
    """Extrai o texto preservando blocos de conteúdo sem acionar bibliotecas pesadas de OCR."""
    doc = pymupdf.open(caminho_pdf)
    texto_md = []
    
    for pagina in doc:
        # Extrai os blocos estruturados de texto da página
        blocos = pagina.get_text("blocks")
        for b in blocos:
            conteudo = b[4].strip()
            if conteudo:
                texto_md.append(conteudo)
        texto_md.append("\n\n")
        
    doc.close()
    return "\n".join(texto_md)

def carregar_e_dividir_documentos(pasta_documentos: str):
    print("Carregando e convertendo PDFs para Markdown...")
    documentos_md = []

    for arquivo in os.listdir(pasta_documentos):
        if arquivo.endswith(".pdf"):
            caminho_completo = os.path.join(pasta_documentos, arquivo)
            texto_md = pdf_para_markdown(caminho_completo)
            
            documentos_md.append(
                Document(
                    page_content=texto_md,
                    metadata={"source": arquivo}
                )
            )

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    chunks_estruturados = []
    for doc in documentos_md:
        chunks_doc = markdown_splitter.split_text(doc.page_content)
        for chunk in chunks_doc:
            chunk.metadata.update(doc.metadata)
            chunks_estruturados.append(chunk)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks_finais = text_splitter.split_documents(chunks_estruturados)

    print(f"Total de chunks gerados: {len(chunks_finais)}")
    return chunks_finais