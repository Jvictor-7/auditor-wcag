# Dicionário oficial de Critérios WCAG 2.1 com seus níveis corretos
# Baseado em: https://www.w3.org/WAI/WCAG21/quickref/

WCAG_CRITERIA_LEVELS = {
    # Princípio 1: Perceptível
    "1.1.1": "A",      # Conteúdo Não Textual
    "1.2.1": "A",      # Apenas Áudio e Apenas Vídeo (Pré-gravado)
    "1.2.2": "A",      # Legendas (Pré-gravado)
    "1.2.3": "A",      # Descrição em Áudio ou Mídia Alternativa (Pré-gravado)
    "1.2.4": "AA",     # Legendas (Transmissão ao Vivo)
    "1.2.5": "AA",     # Descrição em Áudio (Pré-gravado)
    "1.3.1": "A",      # Informações e Relações
    "1.3.2": "A",      # Sequência Significativa
    "1.3.3": "A",      # Características Sensórias
    "1.3.4": "AA",     # Orientação
    "1.3.5": "AA",     # Identificar Propósito da Entrada
    "1.3.6": "AAA",    # Identificar Propósito
    "1.4.1": "A",      # Uso de Cor
    "1.4.2": "A",      # Controle de Áudio
    "1.4.3": "AA",     # Contraste Mínimo
    "1.4.4": "AA",     # Redimensionar Texto
    "1.4.5": "AA",     # Imagens de Texto
    "1.4.6": "AAA",    # Contraste Aprimorado
    "1.4.7": "AAA",    # Áudio de Fundo Baixo ou Ausente
    "1.4.8": "AAA",    # Apresentação Visual
    "1.4.9": "AAA",    # Imagens de Texto (Sem Exceção)
    "1.4.10": "AA",    # Refluxo
    "1.4.11": "AA",    # Contraste de Não-Texto
    "1.4.12": "AA",    # Espaçamento do Texto
    "1.4.13": "AA",    # Conteúdo em Foco Visível

    # Princípio 2: Operável
    "2.1.1": "A",      # Teclado
    "2.1.2": "A",      # Sem Armadilha de Teclado
    "2.1.3": "AAA",    # Teclado (Sem Exceção)
    "2.1.4": "A",      # Atalhos de Caractere
    "2.2.1": "A",      # Limite de Tempo Ajustável
    "2.2.2": "A",      # Pausar, Parar, Ocultar
    "2.2.3": "AAA",    # Sem Limite de Tempo
    "2.2.4": "AAA",    # Interrupções
    "2.2.5": "AAA",    # Reautenticação
    "2.2.6": "AAA",    # Prazos
    "2.3.1": "A",      # Três Flashes ou Abaixo
    "2.3.2": "AAA",    # Três Flashes
    "2.3.3": "AAA",    # Animação de Interações
    "2.4.1": "A",      # Ignorar Blocos
    "2.4.2": "A",      # Título da Página
    "2.4.3": "A",      # Ordem de Foco
    "2.4.4": "A",      # Finalidade do Link (com contexto)
    "2.4.5": "AA",     # Múltiplas Formas
    "2.4.6": "AA",     # Títulos e Rótulos
    "2.4.7": "AA",     # Foco Visível
    "2.4.8": "AAA",    # Localização
    "2.4.9": "AAA",    # Finalidade do Link (Link Apenas)
    "2.4.10": "AAA",   # Títulos de Seção
    "2.5.1": "A",      # Gestos de Ponteiro
    "2.5.2": "A",      # Cancelamento de Ponteiro
    "2.5.3": "A",      # Rótulo em Nome
    "2.5.4": "A",      # Ativação de Movimento
    "2.5.5": "AAA",    # Tamanho do Alvo (Aprimorado)
    "2.5.6": "AAA",    # Ações Simultâneas
    "2.5.7": "AA",     # Gestos Arrastáveis

    # Princípio 3: Compreensível
    "3.1.1": "A",      # Idioma da Página
    "3.1.2": "AA",     # Idioma de Partes
    "3.1.3": "AAA",    # Palavras Incomuns
    "3.1.4": "AAA",    # Abreviaturas
    "3.1.5": "AAA",    # Nível de Leitura
    "3.1.6": "AAA",    # Pronúncia
    "3.2.1": "A",      # Em Foco
    "3.2.2": "A",      # Em Entrada
    "3.2.3": "AA",     # Navegação Consistente
    "3.2.4": "AA",     # Identificação Consistente
    "3.2.5": "AAA",    # Mudança por Solicitação
    "3.3.1": "A",      # Identificação de Erro
    "3.3.2": "A",      # Rótulos ou Instruções
    "3.3.3": "AA",     # Sugestão de Erro
    "3.3.4": "AA",     # Prevenção de Erros (Legal, Financeiro, Dados)
    "3.3.5": "AAA",    # Ajuda
    "3.3.6": "AAA",    # Prevenção de Erros (Todos)
    "3.3.7": "AAA",    # Ajuda Acessível
    "3.3.8": "AAA",    # Validação de Entrada

    # Princípio 4: Robusto
    "4.1.1": "A",      # Análise/Parsing
    "4.1.2": "A",      # Nome, Função, Valor
    "4.1.3": "AA",     # Mensagens de Status
}


def get_criterion_level(criterion_number: str) -> str:
    """
    Retorna o nível correto de um critério WCAG.
    Se não encontrar, retorna '?' para indicar desconhecido.

    Args:
        criterion_number: str no formato "X.X.X" (ex: "1.1.1", "2.4.4")

    Returns:
        str: "A", "AA", "AAA" ou "?" se desconhecido
    """
    return WCAG_CRITERIA_LEVELS.get(criterion_number, "?")
