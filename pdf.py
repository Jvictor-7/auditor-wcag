from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from datetime import datetime
from io import BytesIO
import html
import re

def preparar_texto_para_pdf(texto: str) -> str:
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)

    texto = html.escape(texto)

    texto = texto.replace("&lt;b&gt;", "<b>")
    texto = texto.replace("&lt;/b&gt;", "</b>")
    texto = texto.replace("&lt;br/&gt;", "<br/>")

    texto = texto.replace("\n", "<br/>")

    return texto

def gerar_pdf_relatorio(
    texto: str,
    nome_arquivo_html: str | None = None
) -> BytesIO:

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        alignment=TA_CENTER
    )

    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        spaceAfter=6
    )

    corpo_style = ParagraphStyle(
        "Corpo",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=10
    )

    story = []

    # 🔹 Título
    story.append(Paragraph(
        "Relatório de Acessibilidade WCAG 2.1",
        titulo_style
    ))

    story.append(Spacer(1, 12))

    # 🔹 Metadados
    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")

    story.append(Paragraph(
        f"<b>Data de geração:</b> {data_geracao}",
        meta_style
    ))

    if nome_arquivo_html:
        story.append(Paragraph(
            f"<b>Arquivo HTML analisado:</b> {nome_arquivo_html}",
            meta_style
        ))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%"))
    story.append(Spacer(1, 12))

    # 🔹 Corpo do relatório
    for bloco in texto.split("\n\n"):
        safe_text = preparar_texto_para_pdf(bloco)
        story.append(Paragraph(safe_text, corpo_style))
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)

    return buffer
