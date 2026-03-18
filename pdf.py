from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    Table,
    TableStyle,
    KeepTogether,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import cm
from reportlab.lib.colors import (
    HexColor, white, black, grey, lightgrey,
)
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from datetime import datetime
from io import BytesIO
import html
import re


# ============================================================
# Cores do relatório
# ============================================================
COR_A = HexColor("#E74C3C")       # Vermelho - Nível A
COR_AA = HexColor("#F39C12")      # Laranja  - Nível AA
COR_AAA = HexColor("#3498DB")     # Azul     - Nível AAA

COR_PERCEIVABLE = HexColor("#E74C3C")
COR_OPERABLE = HexColor("#F39C12")
COR_UNDERSTANDABLE = HexColor("#2ECC71")
COR_ROBUST = HexColor("#3498DB")

PRINCIPIOS = {
    "1": "Perceptível",
    "2": "Operável",
    "3": "Compreensível",
    "4": "Robusto",
}

CORES_PRINCIPIOS = {
    "1": COR_PERCEIVABLE,
    "2": COR_OPERABLE,
    "3": COR_UNDERSTANDABLE,
    "4": COR_ROBUST,
}


# ============================================================
# Parser do relatório — extrai estatísticas do texto Markdown
# ============================================================
def extrair_estatisticas(texto: str) -> dict:
    """
    Analisa o texto do relatório Markdown e extrai:
    - Lista de critérios encontrados (número, nome, nível)
    - Contagem por nível (A, AA, AAA)
    - Contagem por princípio WCAG (1.x–4.x)
    """
    criterios = []

    # Padrão: ### Critério 1.4.3 – Contraste Mínimo (Nível AA)
    pattern = re.compile(
        r"###?\s*Critério\s+(\d+\.\d+\.\d+)\s*[\u2013\u2014–—-]\s*(.+?)\s*\(Nível\s+(A{1,3})\)",
        re.IGNORECASE,
    )

    for match in pattern.finditer(texto):
        numero = match.group(1)
        nome = match.group(2).strip()
        nivel = match.group(3).upper()
        criterios.append({
            "numero": numero,
            "nome": nome,
            "nivel": nivel,
        })

    # Contagens por nível
    contagem_nivel = {"A": 0, "AA": 0, "AAA": 0}
    for c in criterios:
        if c["nivel"] in contagem_nivel:
            contagem_nivel[c["nivel"]] += 1

    # Contagens por princípio (primeiro dígito do número)
    contagem_principio = {"1": 0, "2": 0, "3": 0, "4": 0}
    for c in criterios:
        principio = c["numero"][0]
        if principio in contagem_principio:
            contagem_principio[principio] += 1

    return {
        "criterios": criterios,
        "total": len(criterios),
        "por_nivel": contagem_nivel,
        "por_principio": contagem_principio,
    }

# ============================================================
# Gráfico de Barras — Distribuição por Princípio WCAG
# ============================================================
def criar_grafico_barras_principios(stats: dict) -> Drawing | None:
    por_principio = stats["por_principio"]
    dados = [por_principio.get(str(i), 0) for i in range(1, 5)]

    if sum(dados) == 0:
        return None

    drawing = Drawing(400, 240)

    titulo = String(200, 220, "Falhas por Princípio WCAG", textAnchor="middle")
    titulo.fontName = "Helvetica-Bold"
    titulo.fontSize = 12
    drawing.add(titulo)

    bc = VerticalBarChart()
    bc.x = 60
    bc.y = 40
    bc.height = 150
    bc.width = 300
    bc.data = [dados]
    bc.categoryAxis.categoryNames = [
        "1 – Perceptível",
        "2 – Operável",
        "3 – Compreensível",
        "4 – Robusto",
    ]
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 8
    bc.categoryAxis.labels.angle = 0
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(dados) + 1
    bc.valueAxis.valueStep = 1
    bc.valueAxis.labelTextFormat = "%d"
    bc.valueAxis.labels.fontName = "Helvetica"
    bc.valueAxis.labels.fontSize = 8

    bc.bars[0].fillColor = COR_PERCEIVABLE

    for i, cor in enumerate([COR_PERCEIVABLE, COR_OPERABLE, COR_UNDERSTANDABLE, COR_ROBUST]):
        bc.bars[(0, i)].fillColor = cor

    drawing.add(bc)

    return drawing


# ============================================================
# Tabela resumo dos critérios encontrados
# ============================================================
def criar_tabela_criterios(stats: dict, styles) -> list:
    criterios = stats["criterios"]
    if not criterios:
        return []

    elements = []

    elements.append(Paragraph(
        "Critérios Identificados",
        ParagraphStyle(
            "TabelaTitulo",
            parent=styles["Heading2"],
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
    ))

    header = ["#", "Critério", "Descrição", "Nível"]
    data = [header]

    for i, c in enumerate(criterios, 1):
        data.append([
            str(i),
            c["numero"],
            Paragraph(c["nome"], ParagraphStyle("cell", fontSize=8, leading=10)),
            c["nivel"],
        ])

    col_widths = [30, 60, 310, 50]

    table = Table(data, colWidths=col_widths, repeatRows=1)

    nivel_cores = {
        "A": HexColor("#FADBD8"),
        "AA": HexColor("#FDEBD0"),
        "AAA": HexColor("#D6EAF8"),
    }

    table_style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2C3E50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]

    for i, c in enumerate(criterios, 1):
        cor_fundo = nivel_cores.get(c["nivel"], lightgrey)
        table_style_cmds.append(("BACKGROUND", (0, i), (-1, i), cor_fundo))

    table.setStyle(TableStyle(table_style_cmds))

    elements.append(table)

    return elements


# ============================================================
# Caixa de resumo rápido (total, A, AA, AAA)
# ============================================================
def criar_resumo_visual(stats: dict) -> Drawing:
    drawing = Drawing(450, 80)

    # Fundo do card
    drawing.add(Rect(0, 0, 450, 70, fillColor=HexColor("#F8F9FA"), strokeColor=HexColor("#DEE2E6"), strokeWidth=1, rx=5))

    # Total
    t1 = String(60, 45, str(stats["total"]), textAnchor="middle")
    t1.fontName = "Helvetica-Bold"
    t1.fontSize = 22
    t1.fillColor = HexColor("#2C3E50")
    drawing.add(t1)

    l1 = String(60, 28, "Total", textAnchor="middle")
    l1.fontName = "Helvetica"
    l1.fontSize = 9
    l1.fillColor = grey
    drawing.add(l1)

    # Separador
    drawing.add(Rect(120, 15, 1, 40, fillColor=HexColor("#DEE2E6"), strokeColor=None))

    # Nível A
    t2 = String(180, 45, str(stats["por_nivel"]["A"]), textAnchor="middle")
    t2.fontName = "Helvetica-Bold"
    t2.fontSize = 22
    t2.fillColor = COR_A
    drawing.add(t2)

    l2 = String(180, 28, "Nível A", textAnchor="middle")
    l2.fontName = "Helvetica"
    l2.fontSize = 9
    l2.fillColor = grey
    drawing.add(l2)

    # Separador
    drawing.add(Rect(240, 15, 1, 40, fillColor=HexColor("#DEE2E6"), strokeColor=None))

    # Nível AA
    t3 = String(300, 45, str(stats["por_nivel"]["AA"]), textAnchor="middle")
    t3.fontName = "Helvetica-Bold"
    t3.fontSize = 22
    t3.fillColor = COR_AA
    drawing.add(t3)

    l3 = String(300, 28, "Nível AA", textAnchor="middle")
    l3.fontName = "Helvetica"
    l3.fontSize = 9
    l3.fillColor = grey
    drawing.add(l3)

    # Separador
    drawing.add(Rect(360, 15, 1, 40, fillColor=HexColor("#DEE2E6"), strokeColor=None))

    # Nível AAA
    t4 = String(410, 45, str(stats["por_nivel"]["AAA"]), textAnchor="middle")
    t4.fontName = "Helvetica-Bold"
    t4.fontSize = 22
    t4.fillColor = COR_AAA
    drawing.add(t4)

    l4 = String(410, 28, "Nível AAA", textAnchor="middle")
    l4.fontName = "Helvetica"
    l4.fontSize = 9
    l4.fillColor = grey
    drawing.add(l4)

    return drawing


# ============================================================
# Formatação de texto Markdown → ReportLab
# ============================================================
def preparar_texto_para_pdf(texto: str) -> str:
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)

    texto = html.escape(texto)

    texto = texto.replace("&lt;b&gt;", "<b>")
    texto = texto.replace("&lt;/b&gt;", "</b>")
    texto = texto.replace("&lt;br/&gt;", "<br/>")

    texto = texto.replace("\n", "<br/>")

    return texto


# ============================================================
# Função principal — gera o PDF completo com gráficos
# ============================================================
def gerar_pdf_relatorio(
    texto: str,
    nome_arquivo_html: str | None = None,
) -> BytesIO:

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        alignment=TA_CENTER,
    )

    subtitulo_style = ParagraphStyle(
        "Subtitulo",
        parent=styles["Heading2"],
        alignment=TA_LEFT,
        spaceBefore=16,
        spaceAfter=8,
    )

    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=6,
    )

    corpo_style = ParagraphStyle(
        "Corpo",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=10,
    )

    story = []

    # --- Título ---
    story.append(Paragraph(
        "Relatório de Acessibilidade WCAG 2.1",
        titulo_style,
    ))
    story.append(Spacer(1, 12))

    # --- Metadados ---
    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(
        f"<b>Data de geração:</b> {data_geracao}",
        meta_style,
    ))
    if nome_arquivo_html:
        story.append(Paragraph(
            f"<b>Arquivo HTML analisado:</b> {nome_arquivo_html}",
            meta_style,
        ))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%"))
    story.append(Spacer(1, 16))

    # --- Extrai estatísticas do relatório ---
    stats = extrair_estatisticas(texto)

    if stats["total"] > 0:
        # --- Resumo visual (cards com totais) ---
        story.append(Paragraph("Resumo da Análise", subtitulo_style))
        story.append(Spacer(1, 6))
        story.append(criar_resumo_visual(stats))
        story.append(Spacer(1, 20))

        # --- Gráficos lado a lado: pizza + barras ---
        grafico_barras = criar_grafico_barras_principios(stats)

        # if grafico_barras:
        #     story.append(Paragraph("Distribuição das Falhas", subtitulo_style))
        #     story.append(Spacer(1, 6))
        #     story.append(Spacer(1, 16))
        #     story.append(grafico_barras)
        #     story.append(Spacer(1, 20))
        if grafico_barras:
            story.append(grafico_barras)
            story.append(Spacer(1, 20))

        # --- Tabela de critérios ---
        tabela = criar_tabela_criterios(stats, styles)
        if tabela:
            story.extend(tabela)
            story.append(Spacer(1, 20))

        story.append(HRFlowable(width="100%"))
        story.append(Spacer(1, 12))

    # --- Corpo do relatório (texto completo) ---
    story.append(Paragraph("Detalhamento das Falhas", subtitulo_style))
    story.append(Spacer(1, 8))

    for bloco in texto.split("\n\n"):
        safe_text = preparar_texto_para_pdf(bloco)
        story.append(Paragraph(safe_text, corpo_style))
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)

    return buffer
