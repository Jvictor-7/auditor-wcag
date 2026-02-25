# pip install langchain==0.1.20 langchain-core==0.1.52 langchain-community==0.0.38 langchain-openai==0.1.7 langchain-text-splitters==0.0.1 chromadb pypdf python-dotenv

import re
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from config import llm, OPENAI_API_KEY

# Função utilitária para validar se o input parece HTM
def is_html_like(text: str) -> bool:
    html_pattern = r"<\s*\w+[^>]*>"
    return bool(re.search(html_pattern, text))

# Carrega o conteúdo da WCAG diretamente do W3C
loader = PyPDFLoader("assets/WCAG21-completo-1-43.pdf")
docs = loader.load()

# Divisão do documento WCAG em chunks
splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
    )

# Divide o documento carregado em vários pedaços menores
chunks = splitter.split_documents(docs)

# Modelo de embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY,
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
Você atua como auditor técnico com foco em análises objetivas, verificáveis e normativamente fundamentadas.
</persona>

<context>
Você receberá:
1. Trechos da WCAG 2.1 (W3C)
2. Um código HTML fornecido pelo usuário
</context>

<task>
Identifique TODOS os problemas de acessibilidade que possam ser comprovados
diretamente a partir do HTML, CSS inline ou scripts presentes no código.
</task>

<rules>
REGRAS OBRIGATÓRIAS:

1. Um critério WCAG só pode ser aplicado se houver EVIDÊNCIA OBJETIVA no código.

2. São consideradas evidências objetivas:
   - Ausência de atributos obrigatórios (alt, lang, label, track, etc.)
   - Uso incorreto de elementos HTML
   - Valores explícitos de CSS (ex: cores, tamanho de fonte, animação)
   - Scripts que definam tempo limite (ex: setTimeout)
   - Conteúdo que produza movimento automático

3. Critérios que dependam exclusivamente de percepção visual humana
   NÃO devem ser aplicados.

4. Critérios AA ou AAA podem ser aplicados se houver
   valores explícitos no código que permitam verificação técnica.

5. Cada critério deve ser listado apenas uma vez por tipo de problema.

6. Cada falha DEVE conter:
   - Descrição objetiva
   - Número exato do critério (ex: 1.4.3)
   - Nível (A, AA ou AAA)
   - Trecho literal do HTML que comprova
   - Correção técnica direta

7. Não use linguagem especulativa ou preventiva.
   Apenas falhas comprováveis.

8. Se não houver evidência suficiente no código,
   o critério NÃO deve ser aplicado.
   
9. Critérios AAA só devem ser aplicados se houver evidência técnica explícita no código
   (ex: valores CSS que violem limites objetivos, ausência explícita de alternativa obrigatória).
   
10. Critérios AAA devem ser aplicados quando houver valores CSS explícitos
que violem limites técnicos definidos na WCAG.

11. Critérios relacionados a mudança de contexto (ex: 3.2.2)
só devem ser aplicados se houver evento explícito como:
onchange, oninput, redirecionamento automático ou submit automático.

12. O número do critério deve corresponder exatamente ao trecho da WCAG fornecido no contexto.
</rules>

<output_format>
Relatório de Acessibilidade

- Liste apenas falhas comprovadas
- Agrupe por critério
- Não inclua observações preventivas
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
    retriever=vectorstore.as_retriever(search_kwargs={"k": 18}),
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

    response = qa_chain.invoke({"input": user_input})
    return response["answer"]
