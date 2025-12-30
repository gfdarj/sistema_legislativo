def obter_ordinal(numero, feminino=False):
    """
    Converte um número inteiro para sua forma ordinal em português.

    Args:
        numero: O número inteiro.
        feminino: Se True, usa o sufixo feminino ('ª').

    Returns:
        Uma string representando o número ordinal.
    """
    if not isinstance(numero, int):
        raise TypeError("O número deve ser um inteiro.")

    if numero < 0:
        sufixo = "º" if not feminino else "ª"
        return f"-{abs(numero)}{sufixo}"

    # Regras básicas para o português
    if numero == 1:
        sufixo = "º" if not feminino else "ª"
    else:
        # Para a maioria dos outros números, o sufixo padrão é 'º'
        sufixo = "º" if not feminino else "ª"
        # Regras mais complexas para números grandes podem ser implementadas
        # se necessário (ex: vigésimo, trigésimo, etc.), mas para
        # a representação numérica com sufixo, esta lógica funciona.

    return f"{numero}{sufixo}"

