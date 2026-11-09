# Agente-Orthus

## Requisitos Préveis

- Python 3.9+ instalado na sua máquina.


## Passo a Passo de Instalação e Execução

### 1. Clonar ou Acessar o Diretório do Projeto

Navegue até a pasta do projeto no terminal:
```bash
cd caminho/para/Agente-Orthus
```


### 2. Criar o Ambiente Virtual (`venv`)

Criar um ambiente virtual isolado para o projeto evita conflitos com outras bibliotecas do sistema.

- **No Windows:**
  ```cmd
  py -m venv venv
  ```
- **No Linux / macOS:**
  ```bash
  python3 -m venv venv
  ```

---

### 3. Ativar o Ambiente Virtual

- **No Windows (Prompt de Comando - `cmd`):**
  ```cmd
  venv\Scripts\activate
  ```
- **No Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **No Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```

> **Nota:** Ao ativar, você verá o prefixo `(venv)` antes do prompt de comando.

---

### 4. Instalar as Dependências

Com o ambiente virtual ativado, instale os pacotes listados no arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

### 5. Executar o Projeto

Com o ambiente devidamente configurado, execute os scripts na ordem recomendada:

1. **Carregar e processar os documentos no banco vetorial:**
   ```bash
   py loader.py
   ```
   *(ou `python loader.py` dependendo do seu SO/sistema)*

2. **Executar a aplicação principal:**
   ```bash
   py main.py
   ```
   *(ou `python main.py`)*

---

## Estrutura de Dependências (`requirements.txt`)

- `chromadb`: Banco de dados vetorial open-source.
- `sentence-transformers`: Modelos para geração de embeddings de texto.
- `langchain`, `langchain-community`, `langchain-text-splitters`: Framework para orquestração de LLMs e divisão de documentos.
- `pypdf`: Leitura e extração de texto de arquivos PDF.
- `torch`: Computação de tensores e suporte para execução de modelos PyTorch.

---

## Desativar o Ambiente Virtual

Quando terminar o trabalho, você pode fechar o ambiente virtual executando:
```bash
deactivate
```