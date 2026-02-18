import streamlit as st
from rag import analyze_html, get_vectorstore_chunks
from pdf import gerar_pdf_relatorio

# ------------------------------------------------
# Cabeçalho
# ------------------------------------------------
st.title("Auditor de Acessibilidade WCAG")
st.markdown(
    """
Este sistema analisa **código HTML** e identifica **falhas de acessibilidade**
com base **exclusiva** nas diretrizes **WCAG 2.1 (W3C)**.
"""
)

uploaded_file = st.file_uploader(
    "Anexar arquivo HTML",
    type=["html", "htm"]
)

nome_arquivo = None

if uploaded_file is not None:
    nome_arquivo = uploaded_file.name
    html_from_file = uploaded_file.read().decode("utf-8", errors="ignore")
    st.session_state["html_input"] = html_from_file

# ------------------------------------------------
# Entrada do usuário
# ------------------------------------------------
html_input = st.text_area(
    "Código HTML",
    height=300,
    value=st.session_state.get("html_input", ""),
)

st.session_state["html_input"] = html_input

# ------------------------------------------------
# Ação
# ------------------------------------------------

col1, col2 = st.columns([3, 1])

with col1:
    if st.button("Analisar Acessibilidade"):
        if not html_input.strip():
            st.warning("⚠️ Preencha o campo com um código ou anexe um arquivo HTML para análise.")
        else:
            with st.spinner("Analisando acessibilidade com base no WCAG..."):
                resultado = analyze_html(html_input)

            st.session_state["resultado"] = resultado

            st.subheader("Relatório de Acessibilidade")
            st.markdown(resultado)

with col2:
    if "resultado" in st.session_state:
        pdf = gerar_pdf_relatorio(
            texto=st.session_state["resultado"],
            nome_arquivo_html=nome_arquivo
            )
        st.download_button(
            label="Baixar Relatório",
            data=pdf,
            file_name="relatorio_acessibilidade_wcag.pdf",
            mime="application/pdf"
        )
    # ------------------------------------------------
# Rodapé
# ------------------------------------------------
st.markdown("---")
st.caption(
    "Baseado nas Diretrizes de Acessibilidade para Conteúdo Web (WCAG 2.1 – W3C)"
)
