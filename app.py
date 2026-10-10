import base64

import streamlit as st

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
AUDITOR_PAGE = "pages/2_auditor.py"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfLGKRmdnCrl-1WUD6t6nIFV_Q22s39-_Nt4Hvj_GLjWJeRlw/viewform?usp=header"  # troque pela URL real

# WCAG 2.4.2: título de página descritivo
st.set_page_config(
    page_title="Início – Auditor de Acessibilidade WCAG",
    page_icon="♿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# WCAG 3.1.1: o Streamlit define lang="en" por padrão. Como o conteúdo está em
# português, ajustamos o idioma do documento via st.html com JavaScript.
st.html(
    "<script>document.documentElement.lang = 'pt-BR';</script>",
    unsafe_allow_javascript=True,
)


def html(markup: str) -> None:
    """Renderiza HTML sem indentação.

    Linhas com 4+ espaços de recuo viram bloco de código no Markdown,
    por isso removemos o recuo de cada linha antes de enviar.
    """
    compact = " ".join(line.strip() for line in markup.strip().splitlines())
    st.markdown(compact, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Ilustração decorativa (SVG embutido, sem texto, ignorada por leitores de tela)
# ---------------------------------------------------------------------------
ILLUSTRATION_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 360">
  <rect x="20" y="20" width="440" height="320" rx="20" fill="#eff6ff" stroke="#1d4ed8" stroke-width="3"/>
  <path d="M20 40a20 20 0 0 1 20-20h400a20 20 0 0 1 20 20v32H20z" fill="#dbeafe"/>
  <circle cx="52" cy="46" r="7" fill="#1d4ed8"/>
  <circle cx="76" cy="46" r="7" fill="#60a5fa"/>
  <circle cx="100" cy="46" r="7" fill="#93c5fd"/>

  <circle cx="64" cy="125" r="16" fill="#15803d"/>
  <path d="M56 125l6 6 11-12" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="98" y="111" width="240" height="14" rx="7" fill="#bfdbfe"/>
  <rect x="98" y="133" width="160" height="10" rx="5" fill="#dbeafe"/>

  <circle cx="64" cy="185" r="16" fill="#15803d"/>
  <path d="M56 185l6 6 11-12" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="98" y="171" width="200" height="14" rx="7" fill="#bfdbfe"/>
  <rect x="98" y="193" width="180" height="10" rx="5" fill="#dbeafe"/>

  <circle cx="64" cy="245" r="16" fill="#b91c1c"/>
  <path d="M57 238l14 14M71 238l-14 14" stroke="#fff" stroke-width="4" stroke-linecap="round"/>
  <rect x="98" y="231" width="260" height="14" rx="7" fill="#bfdbfe"/>
  <rect x="98" y="253" width="120" height="10" rx="5" fill="#dbeafe"/>

  <rect x="44" y="296" width="392" height="16" rx="8" fill="#dbeafe"/>
  <rect x="44" y="296" width="290" height="16" rx="8" fill="#1d4ed8"/>
</svg>
"""
ILLUSTRATION_URI = "data:image/svg+xml;base64," + base64.b64encode(
    ILLUSTRATION_SVG.encode("utf-8")
).decode("ascii")

# ---------------------------------------------------------------------------
# Estilos
# - Sem cores de texto fixas: usa "inherit" para funcionar em tema claro e escuro.
# - Sem opacity em texto (preserva o contraste).
# - Foco visível, alvos de toque de 48px e sem animações.
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
.block-container { max-width: 1200px; padding-top: 3rem; padding-bottom: 3rem; }

.home-title {
  font-size: clamp(2.1rem, 4.5vw, 3.4rem) !important;
  font-weight: 800 !important;
  line-height: 1.15 !important;
  letter-spacing: -0.02em;
  margin: 0 0 1.25rem !important;
  padding: 0 !important;
}
.home-lead {
  font-size: 1.15rem;
  line-height: 1.75;
  max-width: 60ch;
  margin: 0 0 1.75rem;
}

.home-illustration { width: 100%; max-width: 480px; height: auto; display: block; margin-inline: auto; }

.home-section { margin-top: 4rem; }
.home-section h2 {
  font-size: 1.75rem !important;
  font-weight: 700 !important;
  margin: 0 0 1.5rem !important;
  padding: 0 !important;
}

.home-features, .home-steps {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 2rem;
}

.home-features li { border-top: 4px solid #1d4ed8; padding-top: 1.25rem; }
.home-features h3 { font-size: 1.2rem !important; font-weight: 700 !important; margin: 0 0 .5rem !important; padding: 0 !important; }
.home-features p, .home-steps p { margin: 0; line-height: 1.65; max-width: 45ch; }

.home-steps { counter-reset: passo; }
.home-steps li { counter-increment: passo; position: relative; padding-left: 3.5rem; }
.home-steps li::before {
  content: counter(passo);
  position: absolute; left: 0; top: 0;
  width: 2.5rem; height: 2.5rem; border-radius: 50%;
  background: #1d4ed8; color: #ffffff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 1.1rem;
}
.home-steps strong { display: block; font-size: 1.1rem; margin-bottom: .25rem; }

.home-footer { margin-top: 4rem; padding-top: 1.25rem; border-top: 1px solid rgba(128,128,128,.5); font-size: .95rem; }

/* Botões do Streamlit: alvo de toque confortável e foco bem visível */
.stButton button, .stLinkButton a { min-height: 3rem; font-weight: 600; }
.stButton button:focus-visible, .stLinkButton a:focus-visible {
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

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
col_texto, col_imagem = st.columns([1.15, 0.85], gap="large")

with col_texto:
    html(
        """
        <h1 class="home-title">Auditor de Acessibilidade WCAG</h1>
        <p class="home-lead">
          Análise automática de código HTML com base nas diretrizes WCAG 2.1 do W3C.
          Encontre falhas de acessibilidade nos seus projetos e garanta uma experiência
          inclusiva para todas as pessoas.
        </p>
        """
    )

    col_a, col_b = st.columns(2, gap="small")
    with col_a:
        if st.button("Iniciar análise", type="primary", use_container_width=True):
            st.switch_page(AUDITOR_PAGE)
    with col_b:
        # link_button abre em nova aba; avisamos isso no próprio rótulo (WCAG 3.2.5)
        st.link_button(
            "Avaliar experimento (nova aba)",
            FORM_URL,
            use_container_width=True,
        )

with col_imagem:
    # alt vazio: imagem puramente decorativa
    html(f'<img class="home-illustration" src="{ILLUSTRATION_URI}" alt="">')

# ---------------------------------------------------------------------------
# Recursos
# ---------------------------------------------------------------------------
html(
    """
    <section class="home-section" aria-label="Recursos principais">
      <h2>Recursos principais</h2>
      <ul class="home-features" role="list">
        <li>
          <h3>Análise em tempo real</h3>
          <p>Resultados imediatos, gerados com apoio de inteligência artificial.</p>
        </li>
        <li>
          <h3>Relatórios detalhados</h3>
          <p>Baixe um PDF completo com todas as falhas encontradas no seu código.</p>
        </li>
        <li>
          <h3>Baseado na WCAG 2.1</h3>
          <p>Verificações alinhadas às diretrizes de acessibilidade do W3C.</p>
        </li>
      </ul>
    </section>
    """
)

# ---------------------------------------------------------------------------
# Como funciona (conteúdo realmente sequencial → lista ordenada)
# ---------------------------------------------------------------------------
html(
    """
    <section class="home-section" aria-label="Como funciona">
      <h2>Como funciona</h2>
      <ol class="home-steps" role="list">
        <li>
          <strong>Informe o código</strong>
          <p>Envie o HTML que você quer verificar.</p>
        </li>
        <li>
          <strong>Veja as falhas</strong>
          <p>Receba a lista de problemas de acessibilidade encontrados.</p>
        </li>
        <li>
          <strong>Baixe o relatório</strong>
          <p>Guarde o PDF para corrigir o projeto ou compartilhar com a equipe.</p>
        </li>
      </ol>
    </section>
    """
)

# ---------------------------------------------------------------------------
# Rodapé
# ---------------------------------------------------------------------------
html(
    """
    <p class="home-footer">
      Baseado nas Diretrizes de Acessibilidade para Conteúdo Web (WCAG 2.1 – W3C).
    </p>
    """
)
