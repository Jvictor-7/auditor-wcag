# Técnicas de Falha WCAG 2.1 - Documentos auxiliares para enriquecer o vectorstore
# Baseado nas técnicas oficiais de falha do W3C (Failure Techniques)

WCAG_FAILURE_TECHNIQUES = [
    {
        "id": "F65",
        "content": (
            "Técnica de Falha F65 — Critério 1.1.1 Conteúdo Não Textual (Nível A)\n"
            "Falha: Omissão do atributo alt em elementos img, area e input type='image'.\n"
            "Quando uma imagem não possui atributo alt, tecnologias assistivas não conseguem "
            "comunicar o propósito da imagem ao usuário.\n"
            "Aplica-se quando: o elemento <img>, <area> ou <input type='image'> não possui atributo alt.\n"
            "Correção: Adicionar atributo alt com descrição significativa do conteúdo da imagem. "
            "Se a imagem for decorativa, usar alt=\"\"."
        ),
    },
    {
        "id": "F30",
        "content": (
            "Técnica de Falha F30 — Critério 1.1.1 Conteúdo Não Textual (Nível A)\n"
            "Falha: Uso de imagens de texto em vez de texto real para apresentar informação.\n"
            "Quando texto é renderizado como imagem, ele não pode ser redimensionado, "
            "personalizado ou lido corretamente por tecnologias assistivas.\n"
            "Aplica-se quando: imagens contêm texto que transmite informação e não há alternativa em texto real.\n"
            "Correção: Usar texto real com CSS para estilização em vez de imagens de texto."
        ),
    },
    {
        "id": "F2",
        "content": (
            "Técnica de Falha F2 — Critério 1.3.1 Informações e Relações (Nível A)\n"
            "Falha: Uso de mudanças na apresentação de texto para transmitir informação "
            "sem usar a marcação semântica adequada.\n"
            "Exemplo: usar <b> ou CSS para criar títulos visuais sem usar <h1>–<h6>.\n"
            "Aplica-se quando: a estrutura visual não é refletida na estrutura semântica do HTML.\n"
            "Correção: Usar elementos HTML semânticos (h1-h6, ul, ol, table, fieldset, legend) "
            "para expressar a estrutura."
        ),
    },
    {
        "id": "F68",
        "content": (
            "Técnica de Falha F68 — Critério 1.3.1 Informações e Relações / 4.1.2 Nome, Função, Valor (Nível A)\n"
            "Falha: Controle de formulário sem label associado programaticamente.\n"
            "Quando um input, select ou textarea não tem um <label for='id'> correspondente, "
            "aria-label ou aria-labelledby, tecnologias assistivas não identificam o propósito do campo.\n"
            "Aplica-se quando: elementos de formulário (input, select, textarea) não possuem "
            "rótulo associado programaticamente.\n"
            "Correção: Associar <label for='id_do_campo'> ou usar aria-label/aria-labelledby."
        ),
    },
    {
        "id": "F86",
        "content": (
            "Técnica de Falha F86 — Critério 4.1.2 Nome, Função, Valor (Nível A)\n"
            "Falha: Nome acessível não fornecido para controles de formulário como botões.\n"
            "Quando um <button> está vazio (sem texto, sem aria-label, sem aria-labelledby, "
            "sem title), tecnologias assistivas não podem comunicar sua função.\n"
            "Aplica-se quando: botões não possuem conteúdo textual ou atributos alternativos para nome acessível.\n"
            "Correção: Adicionar texto ao botão, ou usar aria-label ou aria-labelledby."
        ),
    },
    {
        "id": "F89",
        "content": (
            "Técnica de Falha F89 — Critério 2.4.4 Finalidade do Link (Nível A)\n"
            "Falha: Uso de texto genérico em links como 'clique aqui', 'saiba mais', 'leia mais'.\n"
            "Quando o texto do link não descreve seu destino ou propósito, "
            "o usuário não consegue entender para onde o link leva sem contexto visual.\n"
            "Aplica-se quando: o texto do link é genérico e não possui aria-label, "
            "aria-labelledby ou title que complemente.\n"
            "Correção: Usar texto descritivo no link. Ex: 'Ver catálogo de produtos' em vez de 'Clique aqui'."
        ),
    },
    {
        "id": "F91",
        "content": (
            "Técnica de Falha F91 — Critério 1.3.1 Informações e Relações (Nível A)\n"
            "Falha: Cabeçalhos (h1-h6) não marcados corretamente ou hierarquia quebrada.\n"
            "Quando a hierarquia de títulos pula níveis (ex: h1 seguido de h3 sem h2), "
            "a estrutura do documento não é compreensível para tecnologias assistivas.\n"
            "Aplica-se quando: a sequência de headings no documento pula níveis.\n"
            "Correção: Manter hierarquia sequencial. h1 > h2 > h3 sem pular níveis."
        ),
    },
    {
        "id": "F62",
        "content": (
            "Técnica de Falha F62 — Critério 1.3.1 Informações e Relações (Nível A)\n"
            "Falha: Grupo de controles de formulário relacionados sem fieldset e legend.\n"
            "Quando radio buttons ou checkboxes relacionados não estão agrupados com "
            "<fieldset> e <legend>, a relação entre os controles não é comunicada.\n"
            "Aplica-se quando: controles de formulário relacionados (radio, checkbox) "
            "não estão dentro de <fieldset> com <legend>.\n"
            "Correção: Envolver controles relacionados em <fieldset> com <legend> descritivo."
        ),
    },
    {
        "id": "F25",
        "content": (
            "Técnica de Falha F25 — Critério 2.4.2 Título da Página (Nível A)\n"
            "Falha: Página web sem elemento <title> ou com <title> vazio.\n"
            "Quando a página não possui título, tecnologias assistivas e navegadores "
            "não conseguem identificar o conteúdo da página.\n"
            "Aplica-se quando: o elemento <title> está ausente do <head> ou está vazio.\n"
            "Correção: Adicionar <title> descritivo e único dentro do <head>."
        ),
    },
    {
        "id": "F22",
        "content": (
            "Técnica de Falha F22 — Critério 3.2.5 Mudança por Solicitação (Nível AAA) / "
            "3.2.1 Em Foco (Nível A)\n"
            "Falha: Abertura de novas janelas sem solicitação do usuário.\n"
            "Quando uma página abre janelas popup ou redireciona automaticamente ao carregar "
            "ou ao focar em um elemento, isso causa mudança de contexto inesperada.\n"
            "Aplica-se quando: window.open() é chamado em onload, onfocus, ou sem ação explícita do usuário.\n"
            "Correção: Permitir que o usuário inicie a abertura de novas janelas explicitamente. "
            "Adicionar target='_blank' com aviso prévio quando necessário."
        ),
    },
    {
        "id": "F36",
        "content": (
            "Técnica de Falha F36 — Critério 3.2.2 Em Entrada (Nível A)\n"
            "Falha: Envio automático de formulário ao alterar valor de select ou input.\n"
            "Quando um formulário é submetido automaticamente via onchange em <select> "
            "ou oninput, o usuário perde controle sobre quando os dados são enviados.\n"
            "Aplica-se quando: onchange, oninput ou eventos similares disparam submit automaticamente.\n"
            "Correção: Fornecer botão de envio explícito para o formulário."
        ),
    },
    {
        "id": "F88",
        "content": (
            "Técnica de Falha F88 — Critério 1.4.8 Apresentação Visual (Nível AAA)\n"
            "Falha: Texto justificado (text-align: justify) que cria espaçamento irregular.\n"
            "Texto justificado pode criar 'rios de espaço em branco' que dificultam "
            "a leitura para pessoas com dificuldades cognitivas ou visuais.\n"
            "Aplica-se quando: CSS contém text-align: justify.\n"
            "Correção: Usar text-align: left (ou start) para texto corrido."
        ),
    },
    {
        "id": "F24",
        "content": (
            "Técnica de Falha F24 — Critério 1.4.3 Contraste Mínimo (Nível AA) / "
            "1.4.6 Contraste Aprimorado (Nível AAA)\n"
            "Falha: Cores de texto e fundo com contraste insuficiente.\n"
            "Critério 1.4.3 (AA): Texto normal precisa de razão de contraste mínima de 4.5:1. "
            "Texto grande (18pt ou 14pt negrito) precisa de 3:1.\n"
            "Critério 1.4.6 (AAA): Texto normal precisa de 7:1. Texto grande precisa de 4.5:1.\n"
            "Aplica-se quando: valores explícitos de color e background-color no CSS "
            "permitem cálculo do contraste.\n"
            "Correção: Ajustar cores para atender às razões de contraste mínimas."
        ),
    },
    {
        "id": "F59",
        "content": (
            "Técnica de Falha F59 — Critério 4.1.2 Nome, Função, Valor (Nível A)\n"
            "Falha: Uso de role='button' ou similar sem suporte completo a teclado.\n"
            "Quando um <div> ou <span> recebe role='button' mas não possui tabindex='0' "
            "e handlers de teclado (onkeypress/onkeydown para Enter/Space), "
            "ele não é operável por teclado.\n"
            "Aplica-se quando: elementos com role interativo não possuem tabindex e handlers de teclado.\n"
            "Correção: Adicionar tabindex='0' e handlers de teclado, ou usar <button> nativo."
        ),
    },
    {
        "id": "F3",
        "content": (
            "Técnica de Falha F3 — Critério 1.1.1 Conteúdo Não Textual (Nível A)\n"
            "Falha: Link com imagem como único conteúdo, onde a imagem não possui alt.\n"
            "Quando um <a> contém apenas um <img> sem alt, o link não possui nome acessível "
            "e tecnologias assistivas comunicam apenas 'link' ou o URL.\n"
            "Aplica-se quando: <a> contém <img> sem alt como único conteúdo.\n"
            "Correção: Adicionar alt descritivo na imagem dentro do link, descrevendo o destino do link."
        ),
    },
    {
        "id": "F47",
        "content": (
            "Técnica de Falha F47 — Critério 2.2.2 Pausar, Parar, Ocultar (Nível A)\n"
            "Falha: Conteúdo com movimento automático sem mecanismo de pausa.\n"
            "Quando marquee, animações CSS (animation), carrosséis automáticos ou "
            "scripts com setInterval/setTimeout criam movimento sem controle de pausa.\n"
            "Aplica-se quando: há movimento automático no conteúdo sem botão de pausa.\n"
            "Correção: Fornecer mecanismo para pausar, parar ou ocultar o conteúdo em movimento."
        ),
    },
    {
        "id": "F77",
        "content": (
            "Técnica de Falha F77 — Critério 4.1.1 Análise/Parsing (Nível A)\n"
            "Falha: IDs duplicados no mesmo documento HTML.\n"
            "Quando múltiplos elementos possuem o mesmo valor de id, "
            "labels, aria-labelledby e aria-describedby podem não funcionar corretamente.\n"
            "Aplica-se quando: dois ou mais elementos no HTML possuem o mesmo atributo id.\n"
            "Correção: Garantir que cada id seja único no documento."
        ),
    },
    {
        "id": "F87",
        "content": (
            "Técnica de Falha F87 — Critério 3.1.1 Idioma da Página (Nível A)\n"
            "Falha: Ausência do atributo lang no elemento <html>.\n"
            "Quando o idioma principal da página não é declarado, tecnologias assistivas "
            "como leitores de tela não podem determinar a pronúncia e as regras "
            "linguísticas corretas para o conteúdo.\n"
            "Aplica-se quando: o elemento <html> não possui atributo lang (ou xml:lang em XHTML).\n"
            "Correção: Adicionar lang='pt-BR' (ou idioma correspondente) ao elemento <html>."
        ),
    },
    {
        "id": "F10",
        "content": (
            "Técnica de Falha F10 — Critério 3.3.2 Rótulos ou Instruções (Nível A)\n"
            "Falha: Campo de formulário obrigatório sem indicação programática.\n"
            "Quando um campo é obrigatório mas não possui atributo required ou "
            "aria-required='true', tecnologias assistivas não comunicam essa obrigatoriedade.\n"
            "Um asterisco (*) visual sozinho não é suficiente.\n"
            "Aplica-se quando: campos obrigatórios não possuem required ou aria-required.\n"
            "Correção: Adicionar atributo required ou aria-required='true' aos campos obrigatórios."
        ),
    },
    {
        "id": "F4",
        "content": (
            "Técnica de Falha F4 — Critério 2.2.2 Pausar, Parar, Ocultar (Nível A)\n"
            "Falha: Uso de text-decoration: blink ou elemento <blink> que pisca sem controle.\n"
            "Conteúdo que pisca pode causar distração e ser inacessível.\n"
            "Aplica-se quando: CSS usa text-decoration: blink ou há elemento <blink> ou <marquee>.\n"
            "Correção: Remover efeitos de piscar e fornecer conteúdo estático."
        ),
    },
    {
        "id": "F79",
        "content": (
            "Técnica de Falha F79 — Critério 1.2.1 Apenas Áudio / Apenas Vídeo (Pré-gravado) (Nível A) / "
            "1.2.2 Legendas (Pré-gravado) (Nível A)\n"
            "Falha: Conteúdo de vídeo sem legendas ou transcrição.\n"
            "Quando um <video> não possui elemento <track kind='captions'> ou <track kind='subtitles'>, "
            "pessoas surdas ou com deficiência auditiva não acessam o conteúdo auditivo.\n"
            "Aplica-se quando: elemento <video> não contém <track> para legendas.\n"
            "Correção: Adicionar <track kind='captions' src='legendas.vtt' srclang='pt' label='Português'>."
        ),
    },
]
