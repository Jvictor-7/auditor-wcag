"""
Gerador de relatório de acessibilidade WCAG em PDF acessível (PDF/UA-1).

Por que WeasyPrint e não ReportLab?
-----------------------------------
O ReportLab não gera a "árvore de estrutura" (PDF com tags): sem ela, leitores
de tela não sabem o que é título, parágrafo, lista ou tabela, e gráficos
desenhados são invisíveis para eles. O WeasyPrint transforma HTML semântico em
PDF com tags e suporta o perfil PDF/UA (`pdf_variant="pdf/ua-1"`).

Dependência:  pip install "weasyprint>=63"
"""

from __future__ import annotations

import html
import re
from datetime import datetime
from io import BytesIO

# ============================================================
# Constantes
# ============================================================
TITULO_RELATORIO = "Relatório de Acessibilidade WCAG 2.1"

PRINCIPIOS = {
    "1": "Perceptível",
    "2": "Operável",
    "3": "Compreensível",
    "4": "Robusto",
}

# Cores de preenchimento das barras (contraste >= 3:1 com o fundo branco)
CORES_PRINCIPIOS = {
    "1": "#D92D20",
    "2": "#C4570B",
    "3": "#067647",
    "4": "#1570EF",
}
CORES_NIVEIS = {
    "A": "#D92D20",
    "AA": "#C4570B",
    "AAA": "#1570EF",
}


# ============================================================
# Parser do relatório — extrai estatísticas do texto Markdown
# ============================================================
def extrair_estatisticas(texto: str) -> dict:
    """
    Extrai do Markdown: lista de critérios (número, nome, nível),
    contagem por nível (A, AA, AAA) e por princípio WCAG (1–4).
    """
    criterios = []

    # Padrão: ### Critério 1.4.3 – Contraste Mínimo (Nível AA)
    pattern = re.compile(
        r"###?\s*Critério\s+(\d+\.\d+\.\d+)\s*[\u2013\u2014\-]\s*(.+?)\s*\(Nível\s+(A{1,3})\)",
        re.IGNORECASE,
    )

    for match in pattern.finditer(texto):
        criterios.append({
            "numero": match.group(1),
            "nome": match.group(2).strip(),
            "nivel": match.group(3).upper(),
        })

    por_nivel = {"A": 0, "AA": 0, "AAA": 0}
    por_principio = {"1": 0, "2": 0, "3": 0, "4": 0}
    for c in criterios:
        if c["nivel"] in por_nivel:
            por_nivel[c["nivel"]] += 1
        if c["numero"][0] in por_principio:
            por_principio[c["numero"][0]] += 1

    return {
        "criterios": criterios,
        "total": len(criterios),
        "por_nivel": por_nivel,
        "por_principio": por_principio,
    }


# ============================================================
# Markdown -> HTML semântico
# ============================================================
def _inline(texto: str) -> str:
    """Escapa HTML e converte **negrito**, *itálico* e `código`."""
    t = html.escape(texto.strip(), quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    return t


def _celulas_tabela_md(linha: str) -> list[str]:
    return [c.strip() for c in linha.strip().strip("|").split("|")]


def markdown_para_html(texto: str, nivel_base: int = 3) -> str:
    """
    Conversor Markdown mínimo, voltado a acessibilidade:
    - níveis de título são normalizados para nunca "pular" níveis
      (os níveis encontrados viram h3, h4, h5... sob o h2 da seção);
    - listas viram <ul>/<ol>; tabelas ganham <th scope="col">;
    - blocos de código viram <pre><code>.
    """
    linhas = texto.splitlines()

    # Mapeia os níveis de título usados no texto para h3, h4, h5, h6 sem lacunas
    usados = sorted({
        len(m.group(1))
        for l in linhas
        if (m := re.match(r"^(#{1,6})\s+\S", l))
    })
    mapa = {n: min(6, nivel_base + i) for i, n in enumerate(usados)}

    saida: list[str] = []
    paragrafo: list[str] = []
    lista_tipo: str | None = None
    tabela: list[list[str]] = []
    em_codigo = False
    codigo: list[str] = []

    def fechar_paragrafo():
        if paragrafo:
            saida.append("<p>" + "<br>".join(_inline(p) for p in paragrafo) + "</p>")
            paragrafo.clear()

    def fechar_lista():
        nonlocal lista_tipo
        if lista_tipo:
            saida.append(f"</{lista_tipo}>")
            lista_tipo = None

    def fechar_tabela():
        if not tabela:
            return
        cab, *corpo = tabela
        h = "".join(f'<th scope="col">{_inline(c)}</th>' for c in cab)
        linhas_html = "".join(
            "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>"
            for r in corpo
        )
        saida.append(
            f'<table class="md"><thead><tr>{h}</tr></thead>'
            f"<tbody>{linhas_html}</tbody></table>"
        )
        tabela.clear()

    def fechar_tudo():
        fechar_paragrafo()
        fechar_lista()
        fechar_tabela()

    for linha in linhas:
        # --- bloco de código ---
        if linha.strip().startswith("```"):
            if em_codigo:
                saida.append("<pre><code>" + html.escape("\n".join(codigo)) + "</code></pre>")
                codigo.clear()
                em_codigo = False
            else:
                fechar_tudo()
                em_codigo = True
            continue
        if em_codigo:
            codigo.append(linha)
            continue

        # --- linha em branco ---
        if not linha.strip():
            fechar_tudo()
            continue

        # --- título ---
        m = re.match(r"^(#{1,6})\s+(.*\S)\s*$", linha)
        if m:
            fechar_tudo()
            n = mapa[len(m.group(1))]
            saida.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
            continue

        # --- separador horizontal ---
        if re.match(r"^\s*([-*_])\1{2,}\s*$", linha):
            fechar_tudo()
            saida.append("<hr>")
            continue

        # --- tabela ---
        if linha.strip().startswith("|"):
            fechar_paragrafo()
            fechar_lista()
            if re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", linha):
                continue  # linha separadora |---|---|
            tabela.append(_celulas_tabela_md(linha))
            continue
        fechar_tabela()

        # --- lista ---
        m_ul = re.match(r"^\s*[-*•]\s+(.*)$", linha)
        m_ol = re.match(r"^\s*\d+[.)]\s+(.*)$", linha)
        if m_ul or m_ol:
            fechar_paragrafo()
            tipo = "ul" if m_ul else "ol"
            if lista_tipo != tipo:
                fechar_lista()
                saida.append(f"<{tipo}>")
                lista_tipo = tipo
            saida.append(f"<li>{_inline((m_ul or m_ol).group(1))}</li>")
            continue

        # --- parágrafo ---
        fechar_lista()
        paragrafo.append(linha)

    if em_codigo and codigo:
        saida.append("<pre><code>" + html.escape("\n".join(codigo)) + "</code></pre>")
    fechar_tudo()

    return "\n".join(saida)


# ============================================================
# Blocos visuais (todos com equivalente textual)
# ============================================================
def _pct(parte: int, total: int) -> int:
    return round(parte * 100 / total) if total else 0


def _html_cards(stats: dict) -> str:
    """Resumo em lista; cada número vem acompanhado do rótulo em texto."""
    n = stats["por_nivel"]
    itens = [
        ("Total", "Critérios com falha", stats["total"], "#101828"),
        ("A", "Nível A", n["A"], CORES_NIVEIS["A"]),
        ("AA", "Nível AA", n["AA"], CORES_NIVEIS["AA"]),
        ("AAA", "Nível AAA", n["AAA"], CORES_NIVEIS["AAA"]),
    ]
    li = "".join(
        f'<li style="border-top-color:{cor}">'
        f'<span class="num">{valor}</span>'
        f'<span class="lbl">{rotulo}</span></li>'
        for _, rotulo, valor, cor in itens
    )
    return f'<ul class="cards">{li}</ul>'


def _html_barras(titulo: str, legenda: str, linhas: list[tuple[str, int, str]], total: int) -> str:
    """
    "Gráfico" de barras feito como TABELA: o dado é lido por leitores de tela
    (célula com número e porcentagem); a barra é só reforço visual.
    """
    corpo = ""
    for rotulo, valor, cor in linhas:
        pct = _pct(valor, total)
        corpo += (
            f'<tr><th scope="row">{html.escape(rotulo)}</th>'
            f'<td class="val">{valor}</td>'
            f'<td class="val">{pct}%</td>'
            f'<td class="barra-cel"><div class="trilho">'
            f'<div class="fill" style="width:{pct}%;background:{cor}"></div>'
            f"</div></td></tr>"
        )
    return (
        f'<table class="barras"><caption>{html.escape(titulo)}</caption>'
        f'<thead><tr><th scope="col">{html.escape(legenda)}</th>'
        f'<th scope="col">Qtde.</th><th scope="col">Proporção</th>'
        f'<th scope="col"><span class="sr">Representação visual</span></th></tr></thead>'
        f"<tbody>{corpo}</tbody></table>"
    )


def _html_tabela_criterios(stats: dict) -> str:
    linhas = ""
    for c in stats["criterios"]:
        nivel = c["nivel"]
        principio = PRINCIPIOS.get(c["numero"][0], "—")
        linhas += (
            f'<tr><th scope="row">{html.escape(c["numero"])}</th>'
            f'<td>{html.escape(c["nome"])}</td>'
            f"<td>{html.escape(principio)}</td>"
            f'<td><span class="pill n{nivel}">Nível {nivel}</span></td></tr>'
        )
    return (
        '<table class="criterios">'
        "<caption>Critérios de sucesso WCAG com falhas identificadas</caption>"
        '<thead><tr><th scope="col">Critério</th><th scope="col">Descrição</th>'
        '<th scope="col">Princípio</th><th scope="col">Nível</th></tr></thead>'
        f"<tbody>{linhas}</tbody></table>"
    )


# ============================================================
# CSS — moderno, contraste AA/AAA, sem depender só de cor
# ============================================================
CSS = """
@page {
  size: A4;
  margin: 18mm 16mm 22mm 16mm;
  @bottom-left {
    content: "Relatório de Acessibilidade WCAG 2.1";
    font: 8.5pt "Inter", "Helvetica Neue", Arial, "DejaVu Sans", sans-serif;
    color: #475467;
  }
  @bottom-right {
    content: "Página " counter(page) " de " counter(pages);
    font: 8.5pt "Inter", "Helvetica Neue", Arial, "DejaVu Sans", sans-serif;
    color: #475467;
  }
}

:root {
  --ink: #101828;
  --muted: #475467;        /* 7.5:1 sobre branco */
  --line: #D0D5DD;
  --soft: #F2F4F7;
  --brand: #1D2939;
  --accent: #1849A9;       /* 8.6:1 sobre branco */
}

* { box-sizing: border-box; }

html {
  font-family: "Inter", "Helvetica Neue", Arial, "DejaVu Sans", sans-serif;
  font-size: 10.5pt;
  line-height: 1.55;
  color: var(--ink);
}
body { margin: 0; }
.sr { position: absolute; left: -9999px; }  /* texto só para leitores de tela */

/* ---------- Cabeçalho ---------- */
header.capa {
  background: var(--brand);
  color: #FFFFFF;                   /* 14:1 */
  border-radius: 10pt;
  padding: 20pt 22pt;
  margin-bottom: 18pt;
}
header.capa .eyebrow {
  margin: 0 0 4pt;
  font-size: 8.5pt;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #D0D5DD;                   /* 9:1 sobre #1D2939 */
}
header.capa h1 {
  margin: 0 0 12pt;
  font-size: 22pt;
  line-height: 1.2;
  font-weight: 700;
}
header.capa dl { margin: 0; font-size: 9.5pt; }
header.capa dt { display: inline; color: #D0D5DD; }
header.capa dt::after { content: ": "; }
header.capa dd { display: inline; margin: 0 14pt 0 0; font-weight: 600; }

/* ---------- Títulos ---------- */
h2 {
  font-size: 15pt;
  margin: 22pt 0 8pt;
  padding-bottom: 5pt;
  border-bottom: 2pt solid var(--accent);
  color: var(--ink);
  break-after: avoid;
}
h3 { font-size: 12.5pt; margin: 16pt 0 5pt; color: var(--accent); break-after: avoid; }
h4 { font-size: 11pt;   margin: 12pt 0 4pt; color: var(--ink);    break-after: avoid; }
h5, h6 { font-size: 10.5pt; margin: 10pt 0 3pt; color: var(--muted); break-after: avoid; }

p { margin: 0 0 8pt; orphans: 3; widows: 3; }
ul, ol { margin: 0 0 8pt; padding-left: 16pt; }
li { margin-bottom: 3pt; }
hr { border: 0; border-top: 1pt solid var(--line); margin: 14pt 0; }
strong { font-weight: 700; }

code, pre {
  font-family: "DejaVu Sans Mono", "Courier New", monospace;
  font-size: 8.5pt;
}
code { background: var(--soft); padding: 1pt 3pt; border-radius: 3pt; }
pre {
  background: var(--soft);
  border: 1pt solid var(--line);
  border-radius: 6pt;
  padding: 8pt 10pt;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  break-inside: avoid;
}
pre code { background: none; padding: 0; }

/* ---------- Cards de resumo ---------- */
ul.cards { list-style: none; display: flex; margin: 0 0 14pt; padding: 0; }
ul.cards li {
  flex: 1;
  margin: 0 8pt 0 0;
  padding: 10pt 12pt;
  background: var(--soft);
  border-top: 3pt solid var(--ink);
  border-radius: 6pt;
  break-inside: avoid;
}
ul.cards li:last-child { margin-right: 0; }
ul.cards .num { display: block; font-size: 22pt; font-weight: 700; line-height: 1.1; }
ul.cards .lbl { display: block; font-size: 8.5pt; color: var(--muted); }

/* ---------- Tabelas ---------- */
table { width: 100%; border-collapse: collapse; margin: 0 0 14pt; font-size: 9.5pt; }
caption {
  caption-side: top;
  text-align: left;
  font-weight: 700;
  font-size: 10.5pt;
  padding-bottom: 6pt;
  color: var(--ink);
}
thead th {
  background: var(--brand);
  color: #FFFFFF;
  text-align: left;
  font-weight: 600;
  padding: 6pt 8pt;
}
tbody th, tbody td {
  padding: 6pt 8pt;
  text-align: left;
  vertical-align: middle;
  border-bottom: 1pt solid var(--line);
}
tbody th { font-weight: 600; }
tbody tr:nth-child(even) { background: #F9FAFB; }
tr { break-inside: avoid; }
thead { display: table-header-group; }   /* repete o cabeçalho a cada página */

.pill {
  display: inline-block;
  padding: 1.5pt 8pt;
  border-radius: 20pt;
  font-size: 8.5pt;
  font-weight: 700;
  white-space: nowrap;
}
.pill.nA   { background: #FEE4E2; color: #7A271A; }  /* 9.3:1 */
.pill.nAA  { background: #FEF0C7; color: #7A2E0E; }  /* 9.0:1 */
.pill.nAAA { background: #D1E9FF; color: #194185; }  /* 8.4:1 */

table.barras td.val { width: 13%; font-variant-numeric: tabular-nums; }
table.barras .barra-cel { width: 40%; }
.trilho { height: 8pt; background: #E4E7EC; border-radius: 4pt; overflow: hidden; }
.fill { height: 8pt; border-radius: 4pt; }

table.md { margin-top: 4pt; }
"""


# ============================================================
# Montagem do HTML
# ============================================================
def construir_html(texto: str, nome_arquivo_html: str | None = None) -> str:
    stats = extrair_estatisticas(texto)
    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")

    meta_extra = ""
    if nome_arquivo_html:
        meta_extra = (
            "<div><dt>Arquivo analisado</dt>"
            f"<dd>{html.escape(nome_arquivo_html)}</dd></div>"
        )

    secao_resumo = ""
    if stats["total"] > 0:
        total = stats["total"]
        barras_principio = _html_barras(
            "Falhas por princípio WCAG",
            "Princípio",
            [
                (f"{k} – {PRINCIPIOS[k]}", stats["por_principio"][k], CORES_PRINCIPIOS[k])
                for k in "1234"
            ],
            total,
        )
        barras_nivel = _html_barras(
            "Falhas por nível de conformidade",
            "Nível",
            [(f"Nível {k}", stats["por_nivel"][k], CORES_NIVEIS[k]) for k in ("A", "AA", "AAA")],
            total,
        )
        secao_resumo = f"""
        <section aria-labelledby="h-resumo">
          <h2 id="h-resumo">Resumo da análise</h2>
          {_html_cards(stats)}
          {barras_principio}
          {barras_nivel}
        </section>
        <section aria-labelledby="h-criterios">
          <h2 id="h-criterios">Critérios identificados</h2>
          {_html_tabela_criterios(stats)}
        </section>
        """

    corpo = markdown_para_html(texto, nivel_base=3)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>{TITULO_RELATORIO}</title>
  <meta name="author" content="Analisador de Acessibilidade">
  <meta name="description" content="Relatório de conformidade com as diretrizes WCAG 2.1, com resumo, critérios identificados e detalhamento das falhas.">
  <meta name="keywords" content="acessibilidade, WCAG 2.1, relatório, conformidade">
  <style>{CSS}</style>
</head>
<body>
  <header class="capa">
    <p class="eyebrow">Auditoria de conformidade</p>
    <h1>{TITULO_RELATORIO}</h1>
    <dl>
      <div><dt>Data de geração</dt><dd>{data_geracao}</dd></div>
      {meta_extra}
    </dl>
  </header>
  <main>
    {secao_resumo}
    <section aria-labelledby="h-detalhe">
      <h2 id="h-detalhe">Detalhamento das falhas</h2>
      {corpo}
    </section>
  </main>
</body>
</html>"""


# ============================================================
# Função principal — mesma assinatura da versão anterior
# ============================================================
def gerar_pdf_relatorio(
    texto: str,
    nome_arquivo_html: str | None = None,
) -> BytesIO:
    from weasyprint import HTML  # import tardio: só exigido ao gerar o PDF

    html_str = construir_html(texto, nome_arquivo_html)
    buffer = BytesIO()

    try:
        # PDF/UA-1: gera a árvore de tags, idioma, título exibido na janela etc.
        HTML(string=html_str).write_pdf(buffer, pdf_variant="pdf/ua-1")
    except TypeError:
        # WeasyPrint < 62 não conhece pdf_variant; ainda gera PDF com tags básicas
        buffer = BytesIO()
        HTML(string=html_str).write_pdf(buffer)

    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    exemplo = """# Relatório

### Critério 1.1.1 – Conteúdo Não Textual (Nível A)
**Problema:** imagens sem texto alternativo.
- `<img src="logo.png">` sem atributo `alt`
- Banner principal sem descrição

### Critério 1.4.3 – Contraste Mínimo (Nível AA)
**Problema:** texto cinza claro sobre fundo branco.

### Critério 2.4.7 – Foco Visível (Nível AA)
Elementos interativos sem indicador de foco.

### Critério 3.3.2 – Rótulos ou Instruções (Nível A)
Campos de formulário sem rótulo associado.

### Critério 4.1.2 – Nome, Função, Valor (Nível A)
Componentes personalizados sem papel ARIA.
"""
    with open("exemplo_relatorio.pdf", "wb") as f:
        f.write(gerar_pdf_relatorio(exemplo, "index.html").getvalue())
    print("Gerado: exemplo_relatorio.pdf")
