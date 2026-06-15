# Documentação Técnica — Melhorias Implementadas no Auditor de Acessibilidade WCAG 2.1

## Sumário

1. [Introdução](#1-introdução)
2. [Melhoria 1 — Otimização do Pipeline RAG](#2-melhoria-1--otimização-do-pipeline-rag)
   - 2.1 [Few-Shot Prompting](#21-few-shot-prompting)
   - 2.2 [Chunking Semântico por Critério WCAG](#22-chunking-semântico-por-critério-wcag)
   - 2.3 [Pré-Análise de HTML com BeautifulSoup](#23-pré-análise-de-html-com-beautifulsoup)
   - 2.4 [Enriquecimento do Vectorstore com Técnicas de Falha WCAG](#24-enriquecimento-do-vectorstore-com-técnicas-de-falha-wcag)
3. [Melhoria 2 — Visualização de Dados no Relatório PDF](#3-melhoria-2--visualização-de-dados-no-relatório-pdf)
   - 3.1 [Parser de Estatísticas do Relatório](#31-parser-de-estatísticas-do-relatório)
   - 3.2 [Cards de Resumo Quantitativo](#32-cards-de-resumo-quantitativo)
   - 3.3 [Gráfico de Pizza — Distribuição por Nível de Conformidade](#33-gráfico-de-pizza--distribuição-por-nível-de-conformidade)
   - 3.4 [Gráfico de Barras — Distribuição por Princípio WCAG](#34-gráfico-de-barras--distribuição-por-princípio-wcag)
   - 3.5 [Tabela de Critérios Identificados](#35-tabela-de-critérios-identificados)
4. [Arquitetura do Sistema Após as Melhorias](#4-arquitetura-do-sistema-após-as-melhorias)
5. [Considerações Finais](#5-considerações-finais)

---

## 1. Introdução

O sistema de auditoria de acessibilidade web utiliza a arquitetura **RAG (Retrieval-Augmented Generation)** para analisar código HTML e identificar violações às diretrizes WCAG 2.1 (Web Content Accessibility Guidelines). O pipeline original consistia em: (a) extração do documento WCAG em PDF, (b) divisão em chunks via splitter genérico, (c) armazenamento vetorial com ChromaDB, (d) recuperação dos chunks mais relevantes e (e) geração do relatório por um LLM (GPT-4o-mini).

Duas melhorias estruturais foram implementadas com o objetivo de aumentar a **precisão da detecção de falhas** e aprimorar a **apresentação dos resultados** ao usuário final. Este documento descreve cada técnica aplicada com fundamentação técnica e detalhamento da implementação.

---

## 2. Melhoria 1 — Otimização do Pipeline RAG

O pipeline RAG foi reestruturado em quatro frentes complementares, cada uma endereçando uma limitação específica do sistema original.

### 2.1 Few-Shot Prompting

#### Fundamentação Teórica

A técnica de **Few-Shot Prompting** (Brown et al., 2020) consiste em fornecer ao modelo de linguagem um pequeno conjunto de exemplos de entrada e saída desejada diretamente no prompt, sem necessidade de fine-tuning. Diferentemente do **Zero-Shot** (em que nenhum exemplo é fornecido) e do **Fine-Tuning** (em que os pesos do modelo são ajustados com dados de treinamento), o Few-Shot opera exclusivamente via **in-context learning** — o modelo infere o padrão esperado a partir dos exemplos fornecidos no próprio contexto da requisição.

No domínio de auditoria de acessibilidade, essa técnica é particularmente eficaz porque:
- O formato de saída desejado é estruturado e repetitivo (critério, falha, evidência, correção);
- O modelo tende a "ancorar" suas respostas no padrão demonstrado, reduzindo alucinações;
- A profundidade técnica da análise pode ser calibrada pelo nível de detalhe dos exemplos.

#### Implementação

Foram inseridos **dois exemplos completos** na seção `<examples>` do prompt template, cada um contendo:

1. **HTML de entrada** com problemas de acessibilidade identificáveis;
2. **Sinais pré-detectados** (oriundos da pré-análise programática, descrita na seção 2.3);
3. **Relatório esperado** no formato exato que o sistema deve produzir.

**Exemplo 1** — demonstra falhas de nível básico:
- Ausência de `lang` no `<html>` (Critério 3.1.1)
- Imagem sem atributo `alt` (Critério 1.1.1)
- Input sem label associado (Critério 1.3.1)
- Botão sem nome acessível (Critério 4.1.2)

**Exemplo 2** — demonstra falhas de estrutura e semântica:
- Hierarquia de headings quebrada (Critério 1.3.1)
- Link com texto genérico (Critério 2.4.4)
- Vídeo sem legendas (Critério 1.2.1)
- Elemento com `role` interativo sem `tabindex` (Critério 4.1.2)

Cada exemplo estabelece o padrão de formatação: título com número do critério e nível, seguido de campos **Falha**, **Evidência** e **Correção**. Isso garante consistência na saída independentemente da complexidade do HTML analisado.

#### Trade-off de Tokens

Os dois exemplos adicionam aproximadamente **1.200 tokens** ao prompt. Considerando que o modelo utilizado (`gpt-4o-mini`) possui janela de contexto de 128.000 tokens, e que os demais elementos do prompt (18 chunks WCAG + sinais + HTML do usuário) ocupam tipicamente entre 8.000 e 15.000 tokens, o custo adicional dos exemplos é marginal e gera benefício desproporcional na qualidade da saída.

---

### 2.2 Chunking Semântico por Critério WCAG

#### Fundamentação Teórica

O processo de **chunking** (segmentação de documentos em fragmentos menores) é uma etapa crítica em sistemas RAG. O método mais comum é o **RecursiveCharacterTextSplitter**, que divide o texto em segmentos de tamanho fixo (medido em caracteres) com sobreposição parcial entre segmentos consecutivos. Embora seja uma abordagem genérica eficaz, ela apresenta uma limitação fundamental: **desconsidera a estrutura semântica do documento**.

No caso da WCAG 2.1, o documento possui estrutura hierárquica bem definida:
- **Princípios** (1 a 4): Perceptível, Operável, Compreensível, Robusto;
- **Diretrizes** (ex: 1.1, 1.2, 2.1);
- **Critérios de Sucesso** (ex: 1.1.1, 1.4.3, 2.1.1), cada um com número, título, nível (A/AA/AAA) e descrição normativa.

Com o splitter genérico (chunk_size=1200, chunk_overlap=200), era frequente que um critério de sucesso fosse **cortado ao meio**, resultando em chunks que começavam no final de um critério e terminavam no início de outro. Quando esses chunks fragmentados eram recuperados pelo vectorstore, o LLM recebia informação incompleta sobre o critério relevante.

#### Implementação

A função `split_by_wcag_criteria()` substitui o splitter genérico por uma estratégia baseada em **expressão regular que detecta limites de critérios WCAG**:

```python
criteria_pattern = r'(?=(?:Critério de Sucesso\s+|Success Criterion\s+)?\d+\.\d+\.\d+[\s\u2013\u2014–—-]+[A-ZÀ-Ú])'
```

Esta regex utiliza **lookahead positivo** (`?=`) para identificar pontos de início de critérios sem consumi-los, capturando variações como:
- "Critério de Sucesso 1.1.1 – Conteúdo Não Textual"
- "1.1.1 – Conteúdo Não Textual"
- "Success Criterion 1.1.1 – Non-text Content"

Após a segmentação, o algoritmo aplica lógica condicional:

1. **Critérios curtos** (≤ 2000 caracteres): mantidos como chunk único, preservando integridade semântica;
2. **Critérios longos** (> 2000 caracteres): subdivididos com o `RecursiveCharacterTextSplitter` como fallback, mas com metadados (`criterion`, `chunk_part`) que identificam a qual critério cada sub-chunk pertence;
3. **Conteúdo geral** (introduções, glossários): segmentado pelo splitter genérico com metadado `type: general`.

Cada `Document` resultante carrega metadados estruturados:

```python
Document(page_content=section, metadata={"criterion": "1.4.3"})
```

Isso permite que, em futuras iterações, o sistema implemente **filtragem por metadados** na etapa de retrieval (ex: buscar apenas chunks de critérios específicos).

---

### 2.3 Pré-Análise de HTML com BeautifulSoup

#### Fundamentação Teórica

No pipeline RAG original, o HTML do usuário era enviado diretamente como query ao vectorstore. Essa abordagem apresenta dois problemas:

1. **Mismatch semântico**: o conteúdo do HTML (tags, atributos, texto) tem baixa similaridade vetorial com o texto normativo da WCAG (que descreve critérios de forma abstrata). Isso resulta em retrieval subótimo — os chunks recuperados podem não corresponder aos critérios relevantes;
2. **Ausência de evidências programáticas**: o LLM precisa deduzir problemas a partir do HTML bruto, tarefa sujeita a erros e omissões quando o código é extenso.

A solução implementada introduz uma camada de **análise estática programática** entre a entrada do usuário e a invocação do RAG. Essa camada utiliza a biblioteca **BeautifulSoup** com o parser **lxml** para percorrer a árvore DOM e extrair **sinais objetivos de acessibilidade**.

#### Sinais Detectados

A função `pre_analyze_html()` verifica **15 categorias de problemas**:

| # | Verificação | Critério WCAG Relacionado |
|---|-------------|---------------------------|
| 1 | Ausência de `lang` no `<html>` | 3.1.1 – Idioma da Página |
| 2 | `<title>` ausente ou vazio | 2.4.2 – Título da Página |
| 3 | `<img>` sem atributo `alt` | 1.1.1 – Conteúdo Não Textual |
| 4 | Link com `<img>` sem `alt` como único conteúdo | 1.1.1 – Conteúdo Não Textual |
| 5 | `<input>` sem `<label>` associado | 1.3.1 / 3.3.2 – Informações e Relações / Rótulos |
| 6 | `<select>` sem `<label>` associado | 1.3.1 / 3.3.2 – Informações e Relações / Rótulos |
| 7 | `<textarea>` sem `<label>` associado | 1.3.1 / 3.3.2 – Informações e Relações / Rótulos |
| 8 | `<button>` sem nome acessível | 4.1.2 – Nome, Função, Valor |
| 9 | `<video>` sem `<track>` | 1.2.1 / 1.2.2 – Legendas |
| 10 | Links com texto genérico ("clique aqui", etc.) | 2.4.4 – Finalidade do Link |
| 11 | Hierarquia de headings (h1–h6) quebrada | 1.3.1 – Informações e Relações |
| 12 | Elemento com `role` interativo sem `tabindex` | 4.1.2 / 2.1.1 – Teclado |
| 13 | IDs duplicados no documento | 4.1.1 – Análise/Parsing |
| 14 | Estilos inline com propriedades de cor | 1.4.3 / 1.4.6 – Contraste |
| 15 | Elementos `<marquee>` ou `<blink>` | 2.2.2 – Pausar, Parar, Ocultar |
| 16 | Radio buttons sem `<fieldset>`/`<legend>` | 1.3.1 – Informações e Relações |

#### Utilização Dupla dos Sinais

Os sinais extraídos são utilizados em **duas etapas distintas**:

**1. Construção de query enriquecida para o vectorstore**

A função `build_retrieval_query()` mapeia cada sinal a termos de busca semanticamente alinhados com o texto da WCAG:

```python
signal_to_criteria = {
    "alt": "critério 1.1.1 conteúdo não textual alternativa texto imagem",
    "label": "critério 1.3.1 informações relações 3.3.2 rótulos instruções formulário",
    ...
}
```

Em vez de usar o HTML como query (baixa similaridade vetorial), o sistema agora busca por termos como "critério 1.1.1 conteúdo não textual alternativa texto imagem", que possuem alta similaridade com os chunks do documento WCAG. Isso resulta em **retrieval significativamente mais preciso**.

**2. Inclusão como evidências no prompt**

Os sinais são formatados como lista e inseridos na seção `<sinais_pre_detectados>` do prompt:

```
- Ausência de atributo lang no elemento <html>
- Imagem sem atributo alt: <img src="logo.png">
- Campo de formulário sem label associado: <input type="text" name="nome">
```

O LLM recebe instrução explícita (regra 13 do prompt) para avaliar cada sinal contra os critérios WCAG fornecidos no contexto. Isso reduz a probabilidade de **omissão de falhas** (falsos negativos) e direciona a análise do modelo para problemas comprovados.

#### Mudança Arquitetural

Esta melhoria exigiu a remoção do `create_retrieval_chain` do LangChain (que automatizava a etapa de retrieval usando o input bruto como query). A nova implementação chama `vectorstore.similarity_search()` diretamente com a query enriquecida, formata manualmente o prompt com os três elementos (sinais, contexto WCAG, HTML) e invoca o LLM via `llm.invoke()`:

```python
relevant_docs = vectorstore.similarity_search(query, k=18)
context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])

formatted_prompt = prompt_template.format(
    context=context,
    input=user_input,
    signals=signals_text,
)

response = llm.invoke(formatted_prompt)
```

Essa abordagem dá controle total sobre o que é buscado e como os elementos são compostos no prompt.

---

### 2.4 Enriquecimento do Vectorstore com Técnicas de Falha WCAG

#### Fundamentação Teórica

O documento normativo da WCAG 2.1 define **o que** cada critério requer, mas é frequentemente abstrato e não descreve cenários concretos de falha. O W3C mantém documentação complementar composta por:

- **Técnicas Suficientes** (ex: G1, G2, H44): métodos aprovados para satisfazer critérios;
- **Técnicas de Falha** (ex: F65, F68, F86): padrões documentados que violam critérios específicos.

As técnicas de falha são particularmente valiosas para auditoria automatizada porque descrevem **padrões objetivos e verificáveis** — exatamente o que o sistema precisa identificar no HTML.

#### Implementação

O arquivo `wcag_techniques.py` contém **21 técnicas de falha** catalogadas no formato:

```python
{
    "id": "F65",
    "content": (
        "Técnica de Falha F65 — Critério 1.1.1 Conteúdo Não Textual (Nível A)\n"
        "Falha: Omissão do atributo alt em elementos img, area e input type='image'.\n"
        "Aplica-se quando: ...\n"
        "Correção: ..."
    ),
}
```

Cada técnica é convertida em um `Document` do LangChain com metadados tipados:

```python
Document(
    page_content=tech["content"],
    metadata={"type": "technique", "technique_id": "F65"},
)
```

Os documentos de técnicas são **concatenados aos chunks da WCAG** antes da criação do vectorstore:

```python
all_chunks = chunks + technique_docs
vectorstore = Chroma.from_documents(documents=all_chunks, embedding=embedding_model)
```

#### Técnicas Incluídas

| ID | Critério | Descrição da Falha |
|----|----------|-------------------|
| F65 | 1.1.1 (A) | Omissão do atributo alt em imagens |
| F30 | 1.1.1 (A) | Uso de imagens de texto |
| F3 | 1.1.1 (A) | Link com imagem sem alt como único conteúdo |
| F2 | 1.3.1 (A) | Apresentação visual sem marcação semântica |
| F68 | 1.3.1 / 4.1.2 (A) | Controle de formulário sem label |
| F62 | 1.3.1 (A) | Grupo de controles sem fieldset/legend |
| F91 | 1.3.1 (A) | Hierarquia de headings quebrada |
| F24 | 1.4.3 (AA) / 1.4.6 (AAA) | Contraste insuficiente |
| F88 | 1.4.8 (AAA) | Texto justificado (text-align: justify) |
| F79 | 1.2.1 / 1.2.2 (A) | Vídeo sem legendas |
| F47 | 2.2.2 (A) | Conteúdo com movimento automático sem pausa |
| F4 | 2.2.2 (A) | Conteúdo piscante (blink/marquee) |
| F25 | 2.4.2 (A) | Página sem título |
| F89 | 2.4.4 (A) | Texto genérico em links |
| F22 | 3.2.1 (A) / 3.2.5 (AAA) | Abertura de janelas sem solicitação |
| F36 | 3.2.2 (A) | Envio automático de formulário |
| F87 | 3.1.1 (A) | Ausência de lang no html |
| F10 | 3.3.2 (A) | Campo obrigatório sem indicação programática |
| F77 | 4.1.1 (A) | IDs duplicados |
| F86 | 4.1.2 (A) | Botão sem nome acessível |
| F59 | 4.1.2 (A) | Role interativo sem suporte a teclado |

Quando o sistema busca chunks relevantes para uma query como "critério 1.1.1 conteúdo não textual alternativa texto imagem", o vectorstore agora retorna **tanto o texto normativo da WCAG quanto a técnica de falha F65**, fornecendo ao LLM contexto completo: a definição do critério e a descrição prática da falha correspondente.

---

## 3. Melhoria 2 — Visualização de Dados no Relatório PDF

O relatório PDF original consistia exclusivamente de texto corrido — o conteúdo gerado pelo LLM, convertido de Markdown para elementos ReportLab. A melhoria adiciona uma **seção de visualização quantitativa** na primeira página do relatório, antes do detalhamento textual das falhas.

### 3.1 Parser de Estatísticas do Relatório

#### Implementação

A função `extrair_estatisticas()` utiliza expressão regular para identificar e extrair informações estruturadas das seções de critérios no texto Markdown gerado pelo LLM:

```python
pattern = re.compile(
    r"###?\s*Critério\s+(\d+\.\d+\.\d+)\s*[\u2013\u2014–—-]\s*(.+?)\s*\(Nível\s+(A{1,3})\)",
    re.IGNORECASE,
)
```

A regex captura três grupos:
1. **Número do critério** (ex: `1.4.3`) — padrão `\d+\.\d+\.\d+`;
2. **Nome do critério** (ex: `Contraste Mínimo`) — texto entre o travessão e o parêntese;
3. **Nível de conformidade** (ex: `AA`) — padrão `A{1,3}`, capturando A, AA ou AAA.

Os caracteres Unicode `\u2013` (en dash), `\u2014` (em dash), `–` e `—` são incluídos no padrão porque o LLM pode gerar qualquer uma dessas variantes como separador.

#### Dados Extraídos

A função retorna um dicionário com quatro chaves:

```python
{
    "criterios": [{"numero": "1.1.1", "nome": "Conteúdo Não Textual", "nivel": "A"}, ...],
    "total": 7,
    "por_nivel": {"A": 5, "AA": 1, "AAA": 1},
    "por_principio": {"1": 3, "2": 2, "3": 1, "4": 1},
}
```

A contagem **por princípio** é derivada do primeiro dígito do número do critério, que corresponde diretamente à nomenclatura da WCAG:
- **1.x.x** → Princípio 1: Perceptível
- **2.x.x** → Princípio 2: Operável
- **3.x.x** → Princípio 3: Compreensível
- **4.x.x** → Princípio 4: Robusto

---

### 3.2 Cards de Resumo Quantitativo

#### Implementação

A função `criar_resumo_visual()` gera um elemento gráfico vetorial (classe `Drawing` do ReportLab) de 450×80 pixels que apresenta quatro indicadores numéricos em formato de **dashboard card**:

| Indicador | Cor | Descrição |
|-----------|-----|-----------|
| Total | Cinza escuro (#2C3E50) | Número total de critérios violados |
| Nível A | Vermelho (#E74C3C) | Falhas de conformidade básica |
| Nível AA | Laranja (#F39C12) | Falhas de conformidade intermediária |
| Nível AAA | Azul (#3498DB) | Falhas de conformidade avançada |

O elemento é composto por:
- Um retângulo de fundo com cor `#F8F9FA` e borda `#DEE2E6` com cantos arredondados (`rx=5`);
- Quatro pares de `String` (número + rótulo), separados por retângulos divisores verticais de 1px.

A escolha de cores segue o padrão semáforo: vermelho para conformidade mínima (nível A), laranja para intermediário (AA) e azul para avançado (AAA). Esse esquema visual permite identificar imediatamente a **gravidade predominante** das falhas encontradas.

---

### 3.3 Gráfico de Pizza — Distribuição por Nível de Conformidade

#### Implementação

A função `criar_grafico_pizza_niveis()` utiliza a classe `Pie` do módulo `reportlab.graphics.charts.piecharts` para gerar um gráfico de setores:

```python
pie = Pie()
pie.data = [5, 1, 1]  # Exemplo: 5 nível A, 1 nível AA, 1 nível AAA
pie.labels = ["Nível A (5)", "Nível AA (1)", "Nível AAA (1)"]
pie.sideLabels = True
```

Cada fatia utiliza a cor correspondente ao nível (vermelho/laranja/azul). A propriedade `sideLabels = True` posiciona os rótulos ao lado externo da pizza com linhas guia, evitando sobreposição de texto em fatias pequenas.

O gráfico é renderizado em um `Drawing` de 360×220 pixels com título centrado "Falhas por Nível WCAG" em Helvetica-Bold 12pt.

**Condição de supressão**: se nenhuma falha for encontrada, a função retorna `None` e o gráfico não é incluído no PDF. Isso evita gráficos vazios em relatórios positivos.

#### Justificativa da Escolha

O gráfico de pizza é adequado para esta visualização porque:
- O número de categorias é fixo e pequeno (3 — A, AA, AAA);
- O objetivo é comparar **proporções relativas** (ex: 70% das falhas são nível A);
- A interpretação visual é imediata mesmo para leitores não técnicos.

---

### 3.4 Gráfico de Barras — Distribuição por Princípio WCAG

#### Implementação

A função `criar_grafico_barras_principios()` utiliza a classe `VerticalBarChart` do ReportLab para apresentar a contagem de falhas agrupada pelos quatro princípios da WCAG:

```python
bc = VerticalBarChart()
bc.data = [[3, 2, 1, 1]]  # Exemplo: Perceptível, Operável, Compreensível, Robusto
bc.categoryAxis.categoryNames = [
    "1 – Perceptível",
    "2 – Operável",
    "3 – Compreensível",
    "4 – Robusto",
]
```

Cada barra recebe cor individual correspondente ao princípio:

| Princípio | Cor | Hex |
|-----------|-----|-----|
| 1 – Perceptível | Vermelho | #E74C3C |
| 2 – Operável | Laranja | #F39C12 |
| 3 – Compreensível | Verde | #2ECC71 |
| 4 – Robusto | Azul | #3498DB |

O eixo Y é configurado com `valueStep = 1` e `labelTextFormat = "%d"` para exibir apenas valores inteiros, adequado à natureza discreta dos dados (contagem de critérios). O valor máximo do eixo é definido como `max(dados) + 1` para manter espaço visual acima da barra mais alta.

#### Justificativa da Escolha

O gráfico de barras é preferível ao gráfico de pizza para esta visualização porque:
- O número de categorias é exatamente 4 (uma para cada princípio);
- O objetivo é comparar **valores absolutos** entre princípios (não proporções);
- Barras verticais facilitam a leitura de diferenças pequenas entre categorias;
- A identificação visual de qual princípio concentra mais falhas é imediata.

---

### 3.5 Tabela de Critérios Identificados

#### Implementação

A função `criar_tabela_criterios()` gera uma tabela formatada com a classe `Table` do ReportLab, listando todos os critérios identificados no relatório:

| Coluna | Largura | Conteúdo |
|--------|---------|----------|
| # | 30pt | Número sequencial |
| Critério | 60pt | Número do critério (ex: 1.4.3) |
| Descrição | 310pt | Nome do critério (ex: Contraste Mínimo) |
| Nível | 50pt | A, AA ou AAA |

A tabela utiliza estilos diferenciados:

**Cabeçalho**: fundo escuro (#2C3E50) com texto branco em Helvetica-Bold 9pt;

**Linhas de dados**: fonte Helvetica 8pt com cor de fundo variável por nível:
- Nível A: rosa claro (#FADBD8)
- Nível AA: pêssego claro (#FDEBD0)
- Nível AAA: azul claro (#D6EAF8)

A propriedade `repeatRows=1` garante que o cabeçalho se repita caso a tabela se estenda por mais de uma página.

A coloração por nível permite identificação visual imediata da severidade de cada falha, reforçando a informação textual da coluna "Nível" com um canal visual redundante — princípio de design de informação que melhora a acessibilidade e a legibilidade do próprio relatório.

---

## 4. Arquitetura do Sistema Após as Melhorias

O fluxo de execução do sistema atualizado é:

```
[HTML do Usuário]
       │
       ▼
[Pré-Análise com BeautifulSoup]  ──→  Lista de sinais objetivos
       │                                       │
       │                                       ▼
       │                          [build_retrieval_query()]
       │                                       │
       │                                       ▼
       │                          [VectorStore (WCAG + Técnicas)]
       │                                       │
       │                                       ▼
       │                          [18 chunks mais relevantes]
       │                                       │
       ▼                                       ▼
[Prompt com Few-Shot + Sinais + Contexto WCAG + HTML]
       │
       ▼
[GPT-4o-mini]
       │
       ▼
[Relatório Markdown]
       │
       ├──→ [Exibição no Streamlit]
       │
       └──→ [Geração de PDF]
                │
                ├── [Parser de Estatísticas]
                │        │
                │        ├── Cards de Resumo
                │        ├── Gráfico de Pizza (Níveis)
                │        ├── Gráfico de Barras (Princípios)
                │        └── Tabela de Critérios
                │
                └── Detalhamento textual das falhas
```

### Arquivos Modificados

| Arquivo | Descrição |
|---------|-----------|
| `rag.py` | Pipeline RAG completo: chunking semântico, pré-análise HTML, query enriquecida, few-shot prompting |
| `pdf.py` | Geração de PDF com parser de estatísticas, gráficos (pizza e barras), cards de resumo, tabela de critérios |
| `wcag_techniques.py` | Base de conhecimento com 21 técnicas de falha WCAG para enriquecimento do vectorstore |

---

## 5. Considerações Finais

As duas melhorias implementadas endereçam aspectos complementares do sistema:

A **otimização do pipeline RAG** atua na **precisão** da detecção, atacando três pontos de falha:
- O retrieval recuperava chunks irrelevantes (resolvido pelo chunking semântico e pela query enriquecida);
- O LLM não tinha referência de formato e profundidade desejados (resolvido pelo few-shot);
- O vectorstore continha apenas texto normativo abstrato (resolvido pela inclusão de técnicas de falha com padrões concretos de violação).

A **visualização de dados no PDF** atua na **comunicação** dos resultados, adicionando camadas visuais que permitem ao leitor compreender instantaneamente o panorama de conformidade antes de entrar nos detalhes técnicos. Os gráficos foram escolhidos com base no tipo de dado apresentado: pizza para proporções (níveis) e barras para comparação absoluta (princípios).

Ambas as melhorias não introduzem dependências externas adicionais ao projeto — BeautifulSoup e lxml já constavam no `requirements.txt`, e os gráficos são gerados com o módulo `reportlab.graphics` já presente como dependência do gerador de PDF.
