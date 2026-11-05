import json
import chromadb
from groq import Groq

class Agente2Recomendacao:
    def __init__(self, groq_api_key: str, caminho_banco="./meu_chromadb", nome_colecao="nr17_base"):
        self.chroma_client = chromadb.PersistentClient(path=caminho_banco)
        self.colecao = self.chroma_client.get_collection(name=nome_colecao)
        self.ia_client = Groq(api_key=groq_api_key)

    def _buscar_no_rag(self, tipo_erro: str) -> str:
        """Busca no ChromaDB as regras sobre o erro encontrado."""
        resultados = self.colecao.query(query_texts=[tipo_erro], n_results=1)
        documentos = resultados.get("documents", [])
        if documentos and len(documentos) > 0:
            item = documentos
            if isinstance(item, list) and len(item) > 0:
                return item
            return str(item)
        return "Diretrizes gerais da NR-17: Manter postura neutra e pescoço alinhado."

    def processar_alerta(self, json_recebido_do_agente_1: str) -> dict:
        """Lê o erro do Agente 1, consulta a NR-17 e gera os alertas/exercícios."""
        dados_alerta = json.loads(json_recebido_do_agente_1)
        issue = dados_alerta.get("issue", "Desvio Postural")
        duration = dados_alerta.get("duration_seconds", 0)
        details = dados_alerta.get("details", "")

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
            "correcao": "Instrução corta de como reajustar o corpo ou o monitor agora para voltar ao ângulo seguro.",
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
        
        if hasattr(resposta, "choices") and len(resposta.choices) > 0:
            texto_json = resposta.choices.message.content
        else:
            texto_json = resposta["choices"]["message"]["content"]
            
        return json.loads(texto_json)
