# pip install langchain==0.1.20 langchain-core==0.1.52 langchain-community==0.0.38 langchain-openai==0.1.7 langchain-text-splitters==0.0.1 chromadb pypdf python-dotenv

import re

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from config import llm, OPENROUTER_API_KEY, OPENROUTER_BASE_URL

def is_html_like(text: str) -> bool:
    html_pattern = r"<\s*\w+[^>]*>"
    return bool(re.search(html_pattern, text))

WCAG_URL = "https://www.w3.org/TR/WCAG21/"

loader = WebBaseLoader(WCAG_URL)
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )

chunks = splitter.split_documents(docs)

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model
)

prompt_template = ("""
<persona>
Você é um Especialista Sênior em Acessibilidade Web certificado em WCAG.
Você atua como auditor técnico e educacional.
</persona>

<task>
Analise o código HTML fornecido pelo usuário e identifique falhas de acessibilidade
com base EXCLUSIVA no conteúdo do contexto (WCAG).
</task>

<instructions>
- Aponte apenas falhas que sejam suportadas pelo contexto
- Para cada falha, informe:
  - Descrição do problema
  - Critério WCAG (ex: 1.1.1)
  - Nível (A, AA ou AAA)
  - Trecho do HTML relacionado
- Utilize linguagem clara e técnica
- NÃO invente regras
- NÃO utilize conhecimento externo
- Se não houver falhas relevantes no contexto, diga:
  "Nenhuma violação identificada com base nos critérios consultados"
</instructions>

<output>
Relatório de Acessibilidade
</output>

<contexto>
{context}
</contexto>

HTML_ANALISADO:
{input}
""")

CUSTOM_PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "input"]
)

stuff_chain = create_stuff_documents_chain(
    llm=llm,
    prompt=CUSTOM_PROMPT
)

qa_chain = create_retrieval_chain(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 6}),
    combine_docs_chain=stuff_chain
)

INVALID_INPUT_MESSAGE = (
    "Entrada inválida: este sistema analisa exclusivamente código HTML "
    "para auditoria de acessibilidade com base nas diretrizes WCAG."
)

def analyze_html(user_input: str) -> str:
    if not is_html_like(user_input):
        return (
            "Entrada inválida: este sistema analisa exclusivamente "
            "código HTML para auditoria de acessibilidade WCAG."
        )

    response = qa_chain.invoke({"input": user_input})
    return response["answer"]
