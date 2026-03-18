# pip install langchain==0.1.20 langchain-core==0.1.52 langchain-community==0.0.38 langchain-openai==0.1.7 langchain-text-splitters==0.0.1 chromadb pypdf python-dotenv beautifulsoup4 lxml

import re
import logging
from collections import Counter

from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

from config import llm, OPENAI_API_KEY
from wcag_techniques import WCAG_FAILURE_TECHNIQUES

logger = logging.getLogger(__name__)


# ============================================================
# Função utilitária para validar se o input parece HTML
# ============================================================
def is_html_like(text: str) -> bool:
    html_pattern = r"<\s*\w+[^>]*>"
    return bool(re.search(html_pattern, text))


# ============================================================
# MELHORIA 2: Chunking semântico por critério WCAG
# ============================================================
def split_by_wcag_criteria(documents: list) -> list:
    """
    Divide os documentos WCAG por limite de critério de sucesso,
    mantendo cada critério como um chunk coeso em vez de cortar
    no meio com splitter genérico.
    """
    full_text = "\n".join([doc.page_content for doc in documents])

    # Padrão para detectar início de critérios WCAG
    # Captura variações como "Critério de Sucesso 1.1.1" ou "1.1.1 Conteúdo Não Textual"
    criteria_pattern = r'(?=(?:Critério de Sucesso\s+|Success Criterion\s+)?\d+\.\d+\.\d+[\s\u2013\u2014–—-]+[A-ZÀ-Ú])'

    sections = re.split(criteria_pattern, full_text)

    criterion_docs = []
    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
    )

    for section in sections:
        section = section.strip()
        if not section:
            continue

        criterion_match = re.match(r'(\d+\.\d+\.\d+)', section)

        if criterion_match:
            criterion_num = criterion_match.group(1)
            if len(section) > 2000:
                sub_chunks = fallback_splitter.split_text(section)
                for i, chunk in enumerate(sub_chunks):
                    criterion_docs.append(Document(
                        page_content=chunk,
                        metadata={"criterion": criterion_num, "chunk_part": i},
                    ))
            else:
                criterion_docs.append(Document(
                    page_content=section,
                    metadata={"criterion": criterion_num},
                ))
        else:
            if len(section) > 200:
                sub_chunks = fallback_splitter.split_text(section)
                for chunk in sub_chunks:
                    criterion_docs.append(Document(
                        page_content=chunk,
                        metadata={"type": "general"},
                    ))

    return criterion_docs


# ============================================================
# Carrega a WCAG e aplica chunking semântico
# ============================================================
loader = PyPDFLoader("assets/WCAG21-completo-1-43.pdf")
docs = loader.load()

chunks = split_by_wcag_criteria(docs)

# ============================================================
# MELHORIA 4: Adiciona Técnicas de Falha WCAG ao vectorstore
# ============================================================
technique_docs = [
    Document(
        page_content=tech["content"],
        metadata={"type": "technique", "technique_id": tech["id"]},
    )
    for tech in WCAG_FAILURE_TECHNIQUES
]

all_chunks = chunks + technique_docs

# Modelo de embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY,
)

# Criação do banco vetorial (WCAG + Técnicas de Falha)
vectorstore = Chroma.from_documents(
    documents=all_chunks,
    embedding=embedding_model,
)


# ============================================================
# MELHORIA 3: Pré-análise HTML com BeautifulSoup
# ============================================================
def pre_analyze_html(html: str) -> list:
    """
    Analisa o HTML com BeautifulSoup e retorna sinais objetivos
    de problemas de acessibilidade detectáveis programaticamente.
    """
    signals = []
    soup = BeautifulSoup(html, "lxml")

    # --- lang no <html> ---
    html_tag = soup.find("html")
    if html_tag and not html_tag.get("lang"):
        signals.append("Ausência de atributo lang no elemento <html>")

    # --- <title> ---
    if not soup.find("title") or not (soup.find("title") and soup.find("title").get_text(strip=True)):
        signals.append("Página sem elemento <title> ou <title> vazio")

    # --- Imagens sem alt ---
    for img in soup.find_all("img"):
        if not img.has_attr("alt"):
            signals.append(f"Imagem sem atributo alt: {str(img)[:100]}")

    # --- Links com imagem sem alt como único conteúdo ---
    for link in soup.find_all("a"):
        imgs = link.find_all("img")
        text = link.get_text(strip=True)
        if imgs and not text:
            for img in imgs:
                if not img.get("alt"):
                    signals.append(f"Link com imagem sem alt como único conteúdo: {str(link)[:120]}")

    # --- Inputs sem label associado ---
    for inp in soup.find_all("input"):
        if inp.get("type") in ("hidden", "submit", "button", "image"):
            continue
        inp_id = inp.get("id")
        has_label = False
        if inp_id:
            has_label = bool(soup.find("label", attrs={"for": inp_id}))
        if not has_label and not inp.get("aria-label") and not inp.get("aria-labelledby"):
            signals.append(f"Campo de formulário sem label associado: {str(inp)[:100]}")

    # --- Select sem label ---
    for select in soup.find_all("select"):
        sel_id = select.get("id")
        has_label = False
        if sel_id:
            has_label = bool(soup.find("label", attrs={"for": sel_id}))
        if not has_label and not select.get("aria-label") and not select.get("aria-labelledby"):
            signals.append(f"Select sem label associado: {str(select)[:100]}")

    # --- Textarea sem label ---
    for ta in soup.find_all("textarea"):
        ta_id = ta.get("id")
        has_label = False
        if ta_id:
            has_label = bool(soup.find("label", attrs={"for": ta_id}))
        if not has_label and not ta.get("aria-label") and not ta.get("aria-labelledby"):
            signals.append(f"Textarea sem label associado: {str(ta)[:100]}")

    # --- Botões sem nome acessível ---
    for btn in soup.find_all("button"):
        text = btn.get_text(strip=True)
        if not text and not btn.get("aria-label") and not btn.get("aria-labelledby") and not btn.get("title"):
            signals.append(f"Botão sem nome acessível: {str(btn)[:100]}")

    # --- Vídeo sem track ---
    for video in soup.find_all("video"):
        if not video.find("track"):
            signals.append(f"Vídeo sem elemento <track> para legendas: {str(video)[:100]}")

    # --- Links com texto genérico ---
    generic_texts = {
        "clique aqui", "saiba mais", "leia mais", "click here",
        "read more", "more", "aqui", "ver mais", "veja mais",
    }
    for link in soup.find_all("a"):
        text = link.get_text(strip=True).lower()
        if text in generic_texts and not link.get("aria-label") and not link.get("aria-labelledby"):
            signals.append(f"Link com texto genérico '{text}': {str(link)[:100]}")

    # --- Hierarquia de headings ---
    headings = soup.find_all(re.compile(r"^h[1-6]$"))
    prev_level = 0
    for h in headings:
        level = int(h.name[1])
        if prev_level > 0 and level > prev_level + 1:
            signals.append(f"Hierarquia de títulos quebrada: {h.name} após h{prev_level}")
        prev_level = level

    # --- Elementos com role interativo sem suporte a teclado ---
    for el in soup.find_all(attrs={"role": True}):
        role = el.get("role")
        if role in ("button", "link", "tab", "menuitem") and not el.get("tabindex"):
            signals.append(f"Elemento com role='{role}' sem tabindex: {str(el)[:100]}")

    # --- IDs duplicados ---
    all_ids = [el.get("id") for el in soup.find_all(id=True)]
    duplicates = [id_val for id_val, count in Counter(all_ids).items() if count > 1]
    for dup in duplicates:
        signals.append(f"ID duplicado no documento: id='{dup}'")

    # --- Estilos inline com cores (sinal para verificação de contraste) ---
    for el in soup.find_all(style=True):
        style = el.get("style", "")
        if "color" in style or "background" in style:
            signals.append(f"Estilo inline com cores (verificar contraste): {str(el)[:120]}")

    # --- Elementos <marquee> ou <blink> ---
    for tag_name in ("marquee", "blink"):
        if soup.find(tag_name):
            signals.append(f"Elemento <{tag_name}> detectado (conteúdo em movimento sem controle)")

    # --- Radio/checkbox sem fieldset ---
    for form in soup.find_all("form"):
        radios = form.find_all("input", attrs={"type": "radio"})
        if radios and not form.find("fieldset"):
            names = {r.get("name") for r in radios if r.get("name")}
            for name in names:
                signals.append(f"Grupo de radio buttons '{name}' sem <fieldset>/<legend>")

    return signals


def build_retrieval_query(signals: list) -> str:
    """
    Constrói uma query enriquecida para o vectorstore baseada nos
    sinais de acessibilidade pré-detectados no HTML.
    """
    signal_to_criteria = {
        "lang": "critério 3.1.1 idioma da página language",
        "title": "critério 2.4.2 título da página page title",
        "alt": "critério 1.1.1 conteúdo não textual alternativa texto imagem",
        "label": "critério 1.3.1 informações relações 3.3.2 rótulos instruções formulário",
        "botão sem nome": "critério 4.1.2 nome função valor button accessible name",
        "track": "critério 1.2.1 1.2.2 legendas mídia vídeo captions",
        "genérico": "critério 2.4.4 finalidade do link link purpose",
        "hierarquia": "critério 1.3.1 informações relações estrutura headings",
        "tabindex": "critério 2.1.1 teclado 4.1.2 nome função valor keyboard",
        "contraste": "critério 1.4.3 contraste mínimo 1.4.6 contraste aprimorado",
        "select": "critério 1.3.1 informações relações 3.3.2 rótulos select",
        "textarea": "critério 1.3.1 informações relações 3.3.2 rótulos textarea",
        "duplicado": "critério 4.1.1 análise parsing ID duplicado",
        "marquee": "critério 2.2.2 pausar parar ocultar movimento automático",
        "blink": "critério 2.2.2 pausar parar ocultar piscar",
        "fieldset": "critério 1.3.1 informações relações agrupamento radio fieldset legend",
        "imagem sem alt como único": "critério 1.1.1 conteúdo não textual link imagem",
    }

    query_parts = []
    for signal in signals:
        signal_lower = signal.lower()
        for keyword, criteria in signal_to_criteria.items():
            if keyword in signal_lower:
                query_parts.append(criteria)
                break

    # Deduplica mantendo ordem
    seen = set()
    unique_parts = []
    for part in query_parts:
        if part not in seen:
            seen.add(part)
            unique_parts.append(part)

    if unique_parts:
        return "WCAG 2.1 acessibilidade web " + " ".join(unique_parts)
    return "WCAG 2.1 critérios de sucesso acessibilidade web auditoria HTML"


# ============================================================
# MELHORIA 1: Prompt com Few-Shot Examples
# ============================================================
prompt_template = """<persona>
Você é um Especialista Sênior em Acessibilidade Web certificado em WCAG 2.1.
Você atua como auditor técnico com foco em análises objetivas, verificáveis e normativamente fundamentadas.
</persona>

<context>
Você receberá:
1. Trechos da WCAG 2.1 (W3C) e técnicas de falha oficiais
2. Sinais de acessibilidade pré-detectados automaticamente no HTML
3. Um código HTML fornecido pelo usuário
</context>

<task>
Identifique TODOS os problemas de acessibilidade que possam ser comprovados
diretamente a partir do HTML, CSS inline ou scripts presentes no código.
Use os sinais pré-detectados como guia — cada sinal aponta para uma possível falha que DEVE ser
avaliada contra os critérios WCAG fornecidos no contexto.
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

13. Cada sinal pré-detectado deve ser avaliado. Se o sinal corresponder a uma falha WCAG
comprovável, inclua no relatório. Se não, ignore-o silenciosamente.
</rules>

<examples>
<example>
<example_html>
```html
<html>
<body>
  <img src="logo.png">
  <form>
    <input type="text" name="nome">
    <button></button>
  </form>
</body>
</html>
```

Sinais pré-detectados:
- Ausência de atributo lang no elemento <html>
- Imagem sem atributo alt: <img src="logo.png">
- Campo de formulário sem label associado: <input type="text" name="nome">
- Botão sem nome acessível: <button></button>
</example_html>

<example_report>
## Relatório de Acessibilidade WCAG 2.1

### Critério 3.1.1 – Idioma da Página (Nível A)
**Falha:** O elemento `<html>` não possui o atributo `lang`, impedindo que tecnologias assistivas identifiquem o idioma do conteúdo.
**Evidência:** `<html>`
**Correção:** Adicionar atributo lang: `<html lang="pt-BR">`

---

### Critério 1.1.1 – Conteúdo Não Textual (Nível A)
**Falha:** Imagem sem texto alternativo. Tecnologias assistivas não conseguem descrever o conteúdo da imagem ao usuário.
**Evidência:** `<img src="logo.png">`
**Correção:** Adicionar atributo alt descritivo: `<img src="logo.png" alt="Logotipo da empresa">`

---

### Critério 1.3.1 – Informações e Relações (Nível A)
**Falha:** Campo de entrada sem rótulo associado programaticamente. A relação entre o campo e seu propósito não é determinável por tecnologias assistivas.
**Evidência:** `<input type="text" name="nome">`
**Correção:** Associar um label: `<label for="nome">Nome</label><input type="text" id="nome" name="nome">`

---

### Critério 4.1.2 – Nome, Função, Valor (Nível A)
**Falha:** Botão sem nome acessível. Tecnologias assistivas não conseguem comunicar a função do botão ao usuário.
**Evidência:** `<button></button>`
**Correção:** Adicionar texto ao botão: `<button>Enviar</button>` ou usar `<button aria-label="Enviar"></button>`
</example_report>
</example>

<example>
<example_html>
```html
<html lang="pt-BR">
<head><title>Loja</title></head>
<body>
  <h1>Produtos</h1>
  <h3>Eletrônicos</h3>
  <a href="/detalhes">Clique aqui</a>
  <video src="demo.mp4"></video>
  <div role="button">Comprar</div>
</body>
</html>
```

Sinais pré-detectados:
- Hierarquia de títulos quebrada: h3 após h1
- Link com texto genérico 'clique aqui': <a href="/detalhes">Clique aqui</a>
- Vídeo sem elemento <track> para legendas: <video src="demo.mp4"></video>
- Elemento com role='button' sem tabindex: <div role="button">Comprar</div>
</example_html>

<example_report>
## Relatório de Acessibilidade WCAG 2.1

### Critério 1.3.1 – Informações e Relações (Nível A)
**Falha:** Hierarquia de títulos quebrada. O elemento `<h3>` aparece diretamente após `<h1>`, pulando o nível `<h2>`. Tecnologias assistivas dependem da hierarquia correta para navegação.
**Evidência:** `<h1>Produtos</h1>` seguido de `<h3>Eletrônicos</h3>`
**Correção:** Ajustar para hierarquia sequencial: `<h2>Eletrônicos</h2>`

---

### Critério 2.4.4 – Finalidade do Link (Nível A)
**Falha:** Link com texto genérico que não descreve seu destino ou propósito fora de contexto.
**Evidência:** `<a href="/detalhes">Clique aqui</a>`
**Correção:** Usar texto descritivo: `<a href="/detalhes">Ver detalhes do produto</a>`

---

### Critério 1.2.1 – Apenas Áudio e Apenas Vídeo (Pré-gravado) (Nível A)
**Falha:** Elemento de vídeo sem legendas ou transcrição. Pessoas com deficiência auditiva não conseguem acessar o conteúdo.
**Evidência:** `<video src="demo.mp4"></video>`
**Correção:** Adicionar track de legendas: `<video src="demo.mp4"><track kind="captions" src="legendas.vtt" srclang="pt" label="Português"></video>`

---

### Critério 4.1.2 – Nome, Função, Valor (Nível A)
**Falha:** Elemento com `role="button"` sem `tabindex`, tornando-o inacessível por teclado.
**Evidência:** `<div role="button">Comprar</div>`
**Correção:** Adicionar tabindex e handlers de teclado: `<div role="button" tabindex="0">Comprar</div>` ou usar elemento nativo: `<button>Comprar</button>`
</example_report>
</example>
</examples>

<output_format>
Relatório de Acessibilidade

- Liste apenas falhas comprovadas
- Agrupe por critério
- Separe cada critério com "---"
- Não inclua observações preventivas
</output_format>

<sinais_pre_detectados>
{signals}
</sinais_pre_detectados>

<contexto_wcag>
{context}
</contexto_wcag>

<html_analisado>
{input}
</html_analisado>
"""


INVALID_INPUT_MESSAGE = (
    "Entrada inválida: este sistema analisa exclusivamente código HTML "
    "para auditoria de acessibilidade com base nas diretrizes WCAG."
)


# Função para obter chunks estruturados
def get_vectorstore_chunks() -> list:
    """
    Retorna lista de chunks do vectorstore formatados para exibição.
    """
    try:
        all_docs = vectorstore.get()
        chunks_data = []

        for i, doc in enumerate(all_docs['documents'], 1):
            chunks_data.append({
                "id": i,
                "content": doc,
                "chars": len(doc),
                "tokens": int(len(doc) / 4),
            })

        return chunks_data
    except Exception as e:
        logger.error(f"Erro ao obter chunks: {e}")
        return []


# ============================================================
# Função principal chamada pelo Streamlit
# ============================================================
def analyze_html(user_input: str) -> str:
    if not is_html_like(user_input):
        return (
            "Entrada inválida: este sistema analisa exclusivamente "
            "código HTML para auditoria de acessibilidade WCAG."
        )

    # MELHORIA 3: Pré-análise do HTML para extrair sinais objetivos
    signals = pre_analyze_html(user_input)
    signals_text = "\n".join(f"- {s}" for s in signals) if signals else "Nenhum sinal pré-detectado."

    # Query enriquecida com base nos sinais detectados
    query = build_retrieval_query(signals)

    # Recupera chunks relevantes da WCAG + Técnicas de Falha
    relevant_docs = vectorstore.similarity_search(query, k=18)
    context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])

    # Monta o prompt com few-shot, sinais, contexto WCAG e HTML
    formatted_prompt = prompt_template.format(
        context=context,
        input=user_input,
        signals=signals_text,
    )

    # Envia para o LLM
    response = llm.invoke(formatted_prompt)
    return response.content
