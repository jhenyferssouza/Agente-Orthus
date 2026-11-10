import os
import sys

# 1. FIX DE CAMINHO: Garante que o sistema encontre a pasta 'src' em qualquer ambiente
if os.path.exists("Agente-Orthus"):
    %cd Agente-Orthus
elif os.path.basename(os.getcwd()) != "Agente-Orthus" and os.path.exists("../Agente-Orthus"):
    %cd ../Agente-Orthus

# Adiciona o diretório atual ao sistema de busca do Python
sys.path.append(os.getcwd())

import json
import chromadb
from groq import Groq

# Importações dos módulos do seu colega que estão na pasta 'src'
from src.embeddings import carregar_modelo_embeddings
from src.reranker import Reranker

class Agente2Recomendacao:
    def __init__(self, groq_api_key: str):
        self.ia_client = Groq(api_key=groq_api_key)
        
        # --- CONFIGURAÇÃO DO RAG + RERANKER DO COLEGA ---
        base_dir = "./base_conhecimento"
        chroma_dir = os.path.join(base_dir, "chroma_db")
        
        # Conectar ao ChromaDB dele
        self.chroma_client = chromadb.PersistentClient(path=chroma_dir)
        self.colecao = self.chroma_client.get_collection(name="base_conhecimento")
        
        # Inicializar os modelos de Embeddings e Reranker dele
        self.embedding_model = carregar_modelo_embeddings()
        self.reranker = Reranker(model_name="BAAI/bge-reranker-base")

    def _buscar_no_rag(self, tipo_erro: str) -> str:
        """Busca no ChromaDB e aplica o Reranker do colega para a IA."""
        try:
            # 1. Gerar o vetor para o erro detectado
            query_vec = self.embedding_model.encode([tipo_erro], normalize_embeddings=True)

            # 2. Busca inicial (Top 20) no ChromaDB
            resultados_iniciais = self.colecao.query(
                query_embeddings=query_vec.tolist(),
                n_results=20
            )

            # CORREÇÃO AQUI: Adicionado [0] para descompactar a lista extra que o ChromaDB gera
            docs_candidatos = resultados_iniciais["documents"][0] if resultados_iniciais.get("documents") else []
            meta_candidatos = resultados_iniciais["metadatas"][0] if resultados_iniciais.get("metadatas") else []

            if not docs_candidatos:
                return "Diretrizes gerais da NR-17: Manter postura neutra e pescoço alinhado."

            # 3. Aplicar o Reranking para pegar os TOP 5 melhores trechos
            resultados_finais = self.reranker.rerank(
                query=tipo_erro,
                documents=docs_candidatos,
                metadatas=meta_candidatos,
                top_k=5
            )

            # 4. Consolidar os 5 trechos em uma única string de texto para o Prompt
            contexto_formatado = ""
            for i, res in enumerate(resultados_finais):
                fonte = res['metadata'].get('source', 'N/A')
                pagina = res['metadata'].get('page', 'N/A')
                trecho = res['document']
                
                contexto_formatado += f"\n--- Documento {i+1} (Fonte: {fonte}, Pág: {pagina}) ---\n{trecho}\n"

            return contexto_formatado if contexto_formatado else "Diretrizes gerais da NR-17: Manter postura neutra e pescoço alinhado."

        except Exception as e:
            print(f"Aviso controlado no processamento RAG + Reranker: {e}")
            return "Diretrizes gerais da NR-17: Manter postura neutra e pescoço alinhado."


            # 3. Aplicar o Reranking para pegar os TOP 5 melhores trechos
            resultados_finais = self.reranker.rerank(
                query=tipo_erro,
                documents=docs_candidatos,
                metadatas=meta_candidatos,
                top_k=5
            )

            # 4. Consolidar os 5 trechos em uma única string de texto para o Prompt
            contexto_formatado = ""
            for i, res in enumerate(resultados_finais):
                fonte = res['metadata'].get('source', 'N/A')
                pagina = res['metadata'].get('page', 'N/A')
                trecho = res['document']
                
                contexto_formatado += f"\n--- Documento {i+1} (Fonte: {fonte}, Pág: {pagina}) ---\n{trecho}\n"

            return contexto_formatado if contexto_formatado else "Diretrizes gerais da NR-17: Manter postura neutra e pescoço alinhado."

        except Exception as e:
            print(f"Aviso controlado no processamento RAG + Reranker: {e}")
            return "Diretrizes gerais da NR-17: Manter postura neutra e pescoço alinhado."

    def processar_alerta(self, json_recebido_do_agente_1: str) -> dict:
        """Lê o erro do Agente 1, consulta a NR-17 e gera os alertas/exercícios."""
        dados_alerta = json.loads(json_recebido_do_agente_1)
        issue = dados_alerta.get("issue", "Desvio Postural")
        duration = dados_alerta.get("duration_seconds", 0)
        details = dados_alerta.get("details", "")

        # Executa a busca integrada com Reranker
        contexto_nr17 = self._buscar_no_rag(issue)

        system_prompt = (
            "Você é um fisioterapeuta do trabalho especialista na lei NR-17. "
            "Gere recomendações baseadas no contexto fornecido. Responda apenas em formato JSON."
        )

        user_prompt = f"""
        [ALERTA DA WEBCAM]
        - Erro detectado: {issue}
        - Tempo na posição: {duration} segundos
        - Ângulo medido: {details}

        [MANUAL TÉCNICO DA NR-17 / CINESIOLOGIA]
        {contexto_nr17}

        Preencha o JSON abaixo estritamente com base nos dados acima (em português):
        {{
            "justificativa": "Por que esse ângulo medido faz mal de acordo com o manual técnico?",
            "correcao": "Instrução curta de como reajustar o corpo ou o monitor agora para voltar ao ângulo seguro.",
            "microexercicio": "Sugestão de um alongamento ativo específico de 15 segundos para a região."
        }}
        """

        resposta = self.ia_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        
        # CORREÇÃO DEFINITIVA DO RETORNO: Verifica dinamicamente se o retorno é Objeto ou Dicionário clássico
        if hasattr(resposta, "choices"):
            texto_json = resposta.choices[0].message.content
        else:
            texto_json = resposta["choices"][0]["message"]["content"]
            
        return json.loads(texto_json)

        # ... (linhas anteriores do método)
        if hasattr(resposta, "choices"):
            texto_json = resposta.choices.message.content
        else:
            texto_json = resposta["choices"]["message"]["content"]
            
        return json.loads(texto_json)
