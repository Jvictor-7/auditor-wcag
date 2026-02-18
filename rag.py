# pip install langchain==0.1.20 langchain-core==0.1.52 langchain-community==0.0.38 langchain-openai==0.1.7 langchain-text-splitters==0.0.1 chromadb pypdf python-dotenv

import re
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from config import llm, OPENROUTER_API_KEY, OPENROUTER_BASE_URL

# Função utilitária para validar se o input parece HTM
def is_html_like(text: str) -> bool:
    html_pattern = r"<\s*\w+[^>]*>"
    return bool(re.search(html_pattern, text))

# Fonte oficial de conhecimento (WCAG 2.1)
WCAG_URL = "https://www.w3.org/TR/WCAG21/"

# Carrega o conteúdo da WCAG diretamente do W3C
loader = WebBaseLoader(WCAG_URL)
docs = loader.load()

# Divisão do documento WCAG em chunks
splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )

# Divide o documento carregado em vários pedaços menores
chunks = splitter.split_documents(docs)

# Modelo de embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

# Criação do banco vetorial dos chunks (ChromaDB)
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model
)

# Prompt de auditoria WCAG
prompt_template = ("""
<persona>
Você é um Especialista Sênior em Acessibilidade Web certificado em WCAG 2.1.
Você atua como auditor técnico, com foco em análises objetivas e verificáveis.
</persona>

<context>
Você receberá:
1. Um trecho do documento oficial WCAG 2.1 (W3C)
2. Um código HTML fornecido pelo usuário
</context>

<task>
Identifique TODOS os problemas de acessibilidade que possam ser detectados diretamente a partir do HTML, com base nas diretrizes da WCAG 2.1.
</task>

<rules>
REGRAS OBRIGATÓRIAS:

1. NÃO aplique critérios que possuam exceções não verificáveis pelo HTML
   (ex: contraste, uso visual de imagens, layout, foco visual)

2. NÃO aplique critérios que dependam de interpretação visual
   
3. NÃO utilize expressões como:
   - "se aplicável"
   - "é importante considerar"
   - "recomenda-se"
   - "pode causar problemas"

4. NÃO aplique critérios que a WCAG explicitamente isente
   (ex: logotipos em imagens de texto ou contraste)

5. Cada falha DEVE conter:
   - Descrição objetiva do problema
   - Critério WCAG exato (ex: 1.1.1)
   - Nível (A, AA ou AAA)
   - Trecho literal do HTML que comprova a falha
   - Sugestão de correção
   
6. Cada falha deve estar diretamente vinculada a um critério WCAG explicitamente identificável no HTML fornecido

6. Se não for possível COMPROVAR a falha apenas com o HTML e o contexto, a falha NÃO deve ser relatada
   
7. Caso haja campos potencialmente obrigatórios (exemplo: password, usuário) não devidamente rotulados, isso deve ser reportado como falha
</rules>

<output_format>
Relatório de Acessibilidade

- Liste apenas falhas comprovadas
- Não inclua avisos preventivos
</output_format>

<contexto_wcag>
{context}
</contexto_wcag>

<html_analisado>
{input}
</html_analisado>
""")

# Criação do template de prompt
CUSTOM_PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "input"]
)

# Cadeia que injeta os documentos WCAG dentro do prompt
stuff_chain = create_stuff_documents_chain(
    llm=llm,
    prompt=CUSTOM_PROMPT
)

# Cadeia RAG final
# 1. Busca os chunks mais relevantes da WCAG
# 2. Injeta no prompt
# 3. Envia para o LLM   
qa_chain = create_retrieval_chain(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 6}),
    combine_docs_chain=stuff_chain
)

INVALID_INPUT_MESSAGE = (
    "Entrada inválida: este sistema analisa exclusivamente código HTML "
    "para auditoria de acessibilidade com base nas diretrizes WCAG."
)

# Função para obter chunks estruturados
def get_vectorstore_chunks() -> list:
    """
    Retorna lista de chunks do vectorstore formatados para exibição.
    
    Returns:
        Lista de dicionários com informações de cada chunk
    """
    try:
        all_docs = vectorstore.get()
        chunks_data = []
        
        for i, doc in enumerate(all_docs['documents'], 1):
            chunks_data.append({
                "id": i,
                "content": doc,
                "chars": len(doc),
                "tokens": int(len(doc) / 4)
            })
        
        return chunks_data
    except Exception as e:
        logger.error(f"Erro ao obter chunks: {e}")
        return []

# Função principal chamada pelo Streamlit
def analyze_html(user_input: str) -> str:
    if not is_html_like(user_input):
        return (
            "Entrada inválida: este sistema analisa exclusivamente "
            "código HTML para auditoria de acessibilidade WCAG."
        )

    # Recupera os documentos mais relevantes para medir o contexto
    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
    retrieved_docs = retriever.invoke(user_input)

    response = qa_chain.invoke({"input": user_input})
    return response["answer"]
