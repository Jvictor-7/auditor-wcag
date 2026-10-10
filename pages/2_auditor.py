import logging
import re

import streamlit as st

from rag import analyze_html
from pdf import gerar_pdf_relatorio

logger = logging.getLogger(__name__)

# WCAG 2.4.2: título de página descritivo
st.set_page_config(
    page_title="Analisar código – Auditor de Acessibilidade WCAG",
    page_icon="♿",
    layout="wide",
)


def html(markup: str) -> None:
    """Renderiza HTML sem indentação (linhas com 4+ espaços viram bloco de código no Markdown)."""
    compact = " ".join(line.strip() for line in markup.strip().splitlines())
    st.markdown(compact, unsafe_allow_html=True)


# ------------------------------------------------
# Idioma da página e tradução do uploader
# ------------------------------------------------
# Observação: <script> dentro de st.markdown NÃO é executado pelo Streamlit.
# Usamos st.html(..., unsafe_allow_javascript=True). (st.components.v1.html está
# deprecado desde a versão 1.56.)
# - WCAG 3.1.1: define lang="pt-BR" (o padrão do Streamlit é "en")
# - WCAG 3.1.2: traduz textos em inglês do uploader e do campo de texto
st.html(
    r"""
<script>
(function () {
  // Funciona tanto se o script rodar na página quanto dentro de um iframe
  var doc = document, win = window;
  try {
    if (window.parent && window.parent !== window && window.parent.document) {
      doc = window.parent.document;
      win = window.parent;
    }
  } catch (e) {}

  doc.documentElement.lang = 'pt-BR';

  var mapa = [
    [/^Browse files?$/i, 'Escolher arquivo'],
    [/^Drag and drop files? here$/i, 'Arraste e solte o arquivo aqui'],
    [/^Limit\s+(.+?)\s+per file/i, 'Limite de $1 por arquivo'],
    [/^Press Ctrl\+Enter to apply$/i, 'Pressione Ctrl+Enter para aplicar']
  ];
  var alvos = '[data-testid="stFileUploader"], [data-testid="stTextArea"]';

  function traduzirTexto(valor) {
    var t = valor.replace(/\u00a0/g, ' ').trim();
    for (var i = 0; i < mapa.length; i++) {
      if (mapa[i][0].test(t)) return t.replace(mapa[i][0], mapa[i][1]);
    }
    return null;
  }

  function traduzir() {
    doc.querySelectorAll(alvos).forEach(function (zona) {
      // textos visíveis
      var walker = doc.createTreeWalker(zona, 4); // 4 = NodeFilter.SHOW_TEXT
      var no;
      while ((no = walker.nextNode())) {
        var novo = traduzirTexto(no.nodeValue);
        if (novo !== null && novo !== no.nodeValue) no.nodeValue = novo;
      }
      // nomes acessíveis (leitores de tela)
      zona.querySelectorAll('[aria-label], [title]').forEach(function (el) {
        ['aria-label', 'title'].forEach(function (attr) {
          var v = el.getAttribute(attr);
          if (!v) return;
          var n = traduzirTexto(v);
          if (n !== null && n !== v) el.setAttribute(attr, n);
        });
      });
    });
  }

  if (win.__wcagObserver) win.__wcagObserver.disconnect();
  win.__wcagObserver = new win.MutationObserver(traduzir);
  win.__wcagObserver.observe(doc.body, {
    childList: true, subtree: true, characterData: true
  });
  traduzir();
})();
</script>
""",
    unsafe_allow_javascript=True,
)

# ------------------------------------------------
# Estilos (mesmo sistema visual da página inicial)
# - Texto herda a cor do tema (claro/escuro) e não usa opacity
# - Bordas de campos com contraste mínimo de 3:1 (WCAG 1.4.11)
# - Foco visível e alvos de toque de 48px
# ------------------------------------------------
st.markdown(
    """
<style>
.block-container { max-width: 1000px; padding-top: 3rem; padding-bottom: 3rem; }

.page-title {
  font-size: clamp(2rem, 4vw, 3rem) !important;
  font-weight: 800 !important;
  line-height: 1.15 !important;
  letter-spacing: -0.02em;
  margin: 0 0 1rem !important;
  padding: 0 !important;
}
.page-lead { font-size: 1.1rem; line-height: 1.7; max-width: 65ch; margin: 0 0 2rem; }
.page-h2 {
  font-size: 1.6rem !important;
  font-weight: 700 !important;
  margin: 2.5rem 0 .5rem !important;
  padding: 0 !important;
}
.page-hint { margin: 0 0 1rem; line-height: 1.6; }
.page-footer { margin-top: 4rem; padding-top: 1.25rem; border-top: 1px solid rgba(128,128,128,.5); font-size: .95rem; }

/* Campos: bordas visíveis */
[data-testid="stFileUploaderDropzone"] { border: 2px dashed #6b7280 !important; }
[data-testid="stTextArea"] [data-baseweb="textarea"] { border: 2px solid #6b7280 !important; }
[data-testid="stTextArea"] textarea {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: .95rem;
  line-height: 1.5;
}

/* Botões: alvo de toque confortável */
.stButton button, .stDownloadButton button { min-height: 3rem; font-weight: 600; padding-inline: 1.5rem; }

/* Foco visível */
.stButton button:focus-visible,
.stDownloadButton button:focus-visible,
[data-testid="stFileUploaderDropzone"] button:focus-visible,
[data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within {
  outline: 3px solid #2563eb !important;
  outline-offset: 3px !important;
}

/* Remove os ícones de link âncora dos títulos */
[data-testid="stHeaderActionElements"],
[data-testid="stHeading"] a[href^="#"],
h1 a[href^="#"], h2 a[href^="#"], h3 a[href^="#"],
h4 a[href^="#"], h5 a[href^="#"], h6 a[href^="#"] {
  display: none !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------
# Funções auxiliares
# ------------------------------------------------
def carregar_arquivo() -> None:
    """Executa quando o usuário anexa/remove um arquivo: copia o conteúdo para o campo de texto."""
    arquivo = st.session_state.get("arquivo_html")
    if arquivo is None:
        st.session_state["nome_arquivo"] = None
        st.session_state["texto_do_arquivo"] = None
        return

    bruto = arquivo.getvalue()
    try:
        texto = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = bruto.decode("latin-1")

    st.session_state["html_input"] = texto
    st.session_state["nome_arquivo"] = arquivo.name
    st.session_state["texto_do_arquivo"] = texto


def ajustar_titulos(markdown: str, nivel_minimo: int = 3) -> str:
    """Rebaixa os títulos do relatório para que fiquem abaixo do h2 da seção (WCAG 1.3.1)."""
    linhas = markdown.splitlines()
    em_codigo = False
    achados = []

    for i, linha in enumerate(linhas):
        if linha.lstrip().startswith(("```", "~~~")):
            em_codigo = not em_codigo
            continue
        if em_codigo:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", linha)
        if m:
            achados.append((i, len(m.group(1)), m.group(2)))

    if not achados:
        return markdown

    deslocamento = nivel_minimo - min(nivel for _, nivel, _ in achados)
    for i, nivel, titulo in achados:
        linhas[i] = "#" * max(1, min(6, nivel + deslocamento)) + " " + titulo
    return "\n".join(linhas)


# ------------------------------------------------
# Cabeçalho
# ------------------------------------------------
html(
    """
    <h1 class="page-title">Auditor de Acessibilidade WCAG</h1>
    <p class="page-lead">
      Este sistema analisa código HTML e identifica falhas de acessibilidade com base
      exclusiva nas diretrizes WCAG 2.1 (W3C).
    </p>
    """
)

# ------------------------------------------------
# Entrada
# ------------------------------------------------
html(
    """
    <h2 class="page-h2">Informe o código HTML</h2>
    <p class="page-hint">Anexe um arquivo .html ou .htm, ou cole o código no campo de texto.</p>
    """
)

st.file_uploader(
    "Anexar arquivo HTML",
    type=["html", "htm"],
    key="arquivo_html",
    on_change=carregar_arquivo,
)

html_input = st.text_area("Código HTML", key="html_input", height=320)

analisar = st.button("Analisar acessibilidade", type="primary")

# ------------------------------------------------
# Ação
# ------------------------------------------------
if analisar:
    if not html_input.strip():
        st.warning("Cole um código HTML ou anexe um arquivo para iniciar a análise.")
    else:
        # só informa o nome do arquivo se o texto ainda for o do arquivo anexado
        nome = (
            st.session_state.get("nome_arquivo")
            if html_input == st.session_state.get("texto_do_arquivo")
            else None
        )

        resultado = None
        pdf = None

        try:
            with st.spinner("Analisando acessibilidade com base na WCAG 2.1..."):
                resultado = analyze_html(html_input)
        except Exception:
            logger.exception("Falha ao analisar o HTML")
            st.error(
                "Não foi possível concluir a análise. Tente novamente em instantes. "
                "Se o problema continuar, verifique se o código HTML está completo."
            )

        if resultado:
            try:
                pdf = gerar_pdf_relatorio(texto=resultado, nome_arquivo_html=nome)
            except Exception:
                logger.exception("Falha ao gerar o PDF")

            st.session_state["resultado"] = resultado
            st.session_state["pdf"] = pdf
            st.session_state["arquivo_analisado"] = nome
            st.success("Análise concluída. O relatório está logo abaixo.")

# ------------------------------------------------
# Relatório (lido do session_state: continua visível após clicar em "Baixar")
# ------------------------------------------------
if st.session_state.get("resultado"):
    html('<h2 class="page-h2">Relatório de acessibilidade</h2>')

    with st.container(border=True):
        arquivo_analisado = st.session_state.get("arquivo_analisado")
        if arquivo_analisado:
            st.markdown(f"Arquivo analisado: **{arquivo_analisado}**")

        if st.session_state.get("pdf"):
            st.download_button(
                label="Baixar relatório em PDF",
                data=st.session_state["pdf"],
                file_name="relatorio_acessibilidade_wcag.pdf",
                mime="application/pdf",
            )
        else:
            st.warning("Não foi possível gerar o PDF desta análise. O relatório continua disponível abaixo.")

        st.markdown(ajustar_titulos(st.session_state["resultado"]))

# ------------------------------------------------
# Rodapé
# ------------------------------------------------
html(
    """
    <p class="page-footer">
      Baseado nas Diretrizes de Acessibilidade para Conteúdo Web (WCAG 2.1 – W3C).
    </p>
    """
)
