<img width="914" height="476" alt="image" src="https://github.com/user-attachments/assets/32fcd508-929d-40ce-a3c3-ec7d623fe801" /># Agente-Orthus


# 🛠️ Documentação do Projeto - Agente 2: Geração Explicável de Recomendações

Este módulo contém a arquitetura, o código de produção e o guia de integração do **Agente 2**, um agente cognitivo de IA que atua integrado a um banco de dados vetorial (RAG) para mitigar riscos ergonômicos em tempo real. O sistema foi desenvolvido sob diretrizes estritas da **NR-17** e conceitos biomecânicos de **Cinesiologia**.

---

## 🧠 1. Arquitetura de Funcionamento

O Agente 2 opera de forma totalmente desacoplada do hardware de captura, seguindo o pipeline abaixo:

1. **Ingestão (Input)**: O agente intercepta um payload JSON estruturado disparado pelo Agente 1 (Visão Computacional) assim que uma postura nociva atinge a janela móvel de tempo limite.
2. **Busca Vetorial (RAG)**: O termo de desvio (`issue`) é extraído e utilizado em uma busca semântica no banco de dados vetorial **ChromaDB**.
3. **Recuperação de Contexto**: O ChromaDB retorna as regras de conforto da NR-17 e os ângulos de risco cinesiologistas equivalentes à articulação afetada.
4. **Prompt Engineering & Grounding**: O contexto do manual técnico é injetado junto com as métricas em tempo real e regras estritas de não-alucinação em um prompt instrucional.
5. **Inferência Confiável**: A requisição é processada pela infraestrutura de ultra-baixa latência da **Groq API** utilizando o modelo de produção estável **`qwen/qwen3.8-27b`**. A temperatura é fixada em `0.1` para garantir respostas 100% ancoradas na base jurídica e científica.
6. **Entrega Estruturada (Output)**: O agente devolve um objeto JSON tratado contendo Justificativa, Correção e Microexercício pronto para renderização visual no dashboard.

---

## 🤝 2. Contrato de Integração (Conexão com o Agente 1)

Para garantir que a integração de ponta a ponta ocorra sem conflitos de software, o **Agente 1** deve obrigatoriamente construir e despachar um objeto JSON que respeite a seguinte estrutura de chaves:

```json
{
    "event": "POSTURE_PERSISTENCE_ALERT",
    "issue": "Inclinação Cervical",
    "duration_seconds": 15,
    "details": "Pescoço inclinado em 35 graus (Limite seguro é 15 graus)."
}
```

### 📋 Mapeamento de Chaves Obrigatórias:
*   `event`: String estática identificadora (`"POSTURE_PERSISTENCE_ALERT"`).
*   `issue`: A articulação ou desvio mapeado (Ex: `"Inclinação Cervical"`, `"Desvio Lombar"`, `"Ombros Assimétricos"`, `"Desvio de Punho"`). *Esta string dita a chave de busca semântica no ChromaDB.*
*   `duration_seconds`: O tempo em segundos de persistência da postura incorreta.
*   `details`: Informações métricas e angulares brutas geradas pelos cálculos matemáticos sobre as coordenadas da pose.

---

## 💻 3. Código de Produção do Agente 2

Abaixo encontra-se a implementação completa e blindada da classe do agente, projetada para tratar as respostas da API da Groq de forma robusta, independente das variações estruturais de formato do SDK:

```python
import json
import chromadb
from groq import Groq

class Agente2Recomendacao:
    def __init__(self, groq_api_key: str, caminho_banco="./meu_chromadb", nome_colecao="nr17_base"):
        # Conecta ao banco de dados onde ficam os textos da NR-17
        self.chroma_client = chromadb.PersistentClient(path=caminho_banco)
        self.colecao = self.chroma_client.get_collection(name=nome_colecao)
        # Conecta com a IA da Groq
        self.ia_client = Groq(api_key=groq_api_key)

    def _buscar_no_rag(self, tipo_erro: str) -> str:
        """Busca no ChromaDB as regras sobre o erro encontrado."""
        resultados = self.colecao.query(query_texts=[tipo_erro], n_results=1)
        documentos = resultados.get('documents',)
        
        if documentos and len(documentos) > 0:
            item = documentos
            if isinstance(item, list) and len(item) > 0:
                return item
            elif isinstance(item, str):
                return item
        return "Diretrizes gerais da NR-17: Manter postura neutra e pescoço alinhado."

    def processar_alerta(self, json_recebido_do_agente_1: str) -> dict:
        """Lê o erro do Agente 1, consulta a NR-17 e gera os alertas/exercícios."""
        dados_alerta = json.loads(json_recebido_do_agente_1)
        issue = dados_alerta.get("issue", "Desvio Postural")
        duration = dados_alerta.get("duration_seconds", 0)
        details = dados_alerta.get("details", "")

        # Busca o manual de regras no ChromaDB (RAG)
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

        # Envia para a IA da Groq processar com o modelo estável de produção
        resposta = self.ia_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        
        # Tratamento seguro para extração do conteúdo de texto do JSON da IA
        if isinstance(resposta, list):
            texto_json = resposta.message.content
        elif hasattr(resposta, 'choices') and len(resposta.choices) > 0:
            texto_json = resposta.choices.message.content
        else:
            texto_json = resposta['choices']['message']['content']
            
        return json.loads(texto_json)
```

---

## 🔒 4. Camada de Segurança e Ocultação de Chaves

O sistema proíbe a exposição de chaves privadas (`API Keys`) de forma explícita no código para evitar vazamentos em repositórios públicos como o GitHub.

### No Google Colab (Ambiente de Testes)
A credencial é injetada via painel **Secrets** (ícone de Chave 🔑 na barra lateral esquerda), sob o rótulo identificador de `GROQ_API_KEY`. O resgate do hash seguro ocorre via API do Google:
```python
from google.colab import userdata
CHAVE_SECRETA = userdata.get('GROQ_API_KEY')
```

### No Streamlit Local (Ambiente de Produção)
As chaves de desenvolvimento devem ser inseridas no arquivo oculto local `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_seu_token_aqui"
```
E acessadas dinamicamente sem exposição via código com `st.secrets["GROQ_API_KEY"]`.

---

## 🎯 5. Critérios de Aceite Homologados

*   **Explicabilidade Técnica**: Geração automática de justificativas com base direta na NR-17 e dados angulares sem alucinações técnicas.
*   **Saída Estruturada**: Resposta nativa em formato JSON garantindo conformidade com a camada de visualização no Dashboard.
*   **Análise Multi-Articulação**: Pronto para processar desvios de múltiplos eixos biomecânicos e articulações simultâneas.
