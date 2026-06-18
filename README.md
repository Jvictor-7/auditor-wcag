# Auditor WCAG 2.1 - Análise de Acessibilidade

Sistema de auditoria de acessibilidade web baseado em RAG (Retrieval-Augmented Generation) com GPT-4o-mini e ChromaDB.

## 🚀 Instalação Rápida

### Requisitos
- Python 3.10+
- Chave de API da OpenAI

### Passos

1. **Clone o repositório:**
```bash
git clone <seu-repo>
cd rag-acessibility
```

2. **Crie um ambiente virtual:**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite .env e adicione sua OPENAI_API_KEY
```

5. **Execute a aplicação:**
```bash
streamlit run app.py
```

## 📊 Como Usar

1. **Cole código HTML** no campo de texto ou **anexe um arquivo .html**
2. Clique em **"Analisar Acessibilidade"**
3. Receba relatório com falhas WCAG identificadas
4. **Baixe o PDF** com gráficos e estatísticas

## 🔧 Arquitetura

- **app.py** - Interface Streamlit
- **rag.py** - Pipeline RAG com ChromaDB + LLM
- **pdf.py** - Geração de relatórios em PDF
- **config.py** - Configuração OpenAI
- **wcag_techniques.py** - Técnicas de falha WCAG
- **requirements.txt** - Dependências Python

## 🐛 Correção Recente (Produção)

### Problema
`sqlite3.OperationalError` ao usar em Streamlit Cloud/Produção

### Causa
ChromaDB criava banco em `/tmp/` que era limpo entre requisições

### Solução ✅
- Implementado `@st.cache_resource` em `load_vectorstore()`
- VectorStore agora persiste na memória da sessão Streamlit
- Suporta múltiplas requisições simultâneas sem conflitos

## 📝 Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```
OPENAI_API_KEY=sk-...
```

## 🤝 Contribuindo

Sinta-se livre para abrir issues e pull requests!

## 📄 Licença

MIT
