import streamlit as st
from rag import analyze_html

st.set_page_config(
    page_title="Auditor WCAG",
    page_icon="",
    layout="wide"
)

# ------------------------------------------------
# Cabeçalho
# ------------------------------------------------
st.title("Auditor de Acessibilidade WCAG")
st.markdown(
    """
Este sistema analisa **código HTML** e identifica **falhas de acessibilidade**
com base **exclusiva** nas diretrizes **WCAG 2.1 (W3C)**.

Cole seu HTML abaixo e clique em **Analisar**.
"""
)

# ------------------------------------------------
# Entrada do usuário
# ------------------------------------------------
html_input = st.text_area(
    "Código HTML",
    height=300,
    placeholder="""
<img src="logo.png">
<form>
  <input type="text">
  <button>Clique aqui</button>
</form>
"""
)

# ------------------------------------------------
# Ação
# ------------------------------------------------
if st.button("Analisar Acessibilidade"):
    if not html_input.strip():
        st.warning("⚠️ Cole um código HTML para análise.")
    else:
        with st.spinner("Analisando acessibilidade com base no WCAG..."):
            resultado = analyze_html(html_input)

        st.subheader("Relatório de Acessibilidade")
        st.markdown(resultado)

# ------------------------------------------------
# Rodapé
# ------------------------------------------------
st.markdown("---")
st.caption(
    "Baseado nas Diretrizes de Acessibilidade para Conteúdo Web (WCAG 2.1 – W3C)"
)
