import re
from typing import Annotated
from pydantic import BaseModel, Field, AfterValidator

CNPJ_REGEX = re.compile(r"^[A-HJ-NP-RT-VWXYZ0-9]{12}[0-9]{2}$")
FORBIDDEN_LETTERS = set("IOUQF")


def normalize_cnpj(value: str) -> str:
    """Remove máscara e converte para maiúsculas."""
    return re.sub(r"[\.\-\/]", "", value).upper()


def is_repeated_sequence(cnpj: str) -> bool:
    """
    Verifica se o CNPJ e composto por caracteres repetidos.
    Parametros:
        cnpj: CNPJ normalizado (string)
    Retorna:
        True se for sequencia repetida, senao False
    """
    return cnpj == cnpj[0] * len(cnpj)


def char_to_value(char: str) -> int:
    """
    Converte caractere alfanumerico em valor numerico do CNPJ.
    Parametros:
        char: Caractere alfanumerico (string)
    Retorna:
        Valor numerico calculado (int)
    """
    if char.isdigit():
        return int(char)
    elif char.isalpha():
        if char in FORBIDDEN_LETTERS:
            raise ValueError(f"Letra proibida no CNPJ: {char}")
        return ord(char) - 48
    else:
        raise ValueError(f"Caractere inválido no CNPJ: {char}")


def calculate_cnpj_dvs(base: str) -> str:
    """
    Calcula os digitos verificadores (DV) do CNPJ.
    Parametros:
        base: Primeiros 12 caracteres do CNPJ (string)
    Retorna:
        Dois digitos verificadores concatenados (string)
    """
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6] + weights1
    sum1 = sum(char_to_value(c) * w for c, w in zip(base, weights1))
    rem1 = sum1 % 11
    dv1 = 0 if rem1 < 2 else 11 - rem1
    sum2 = sum(char_to_value(c) * w for c, w in zip(base + str(dv1), weights2))
    rem2 = sum2 % 11
    dv2 = 0 if rem2 < 2 else 11 - rem2
    return f"{dv1}{dv2}"


def cnpj_validator(value: str) -> str:
    """
    Valida e normaliza um CNPJ, lancando erro em caso invalido.
    Parametros:
        value: CNPJ com ou sem mascara (string)
    Retorna:
        CNPJ normalizado (string)
    """
    norm = normalize_cnpj(value)
    if len(norm) != 14:
        raise ValueError("CNPJ deve ter 14 caracteres (após remover máscara).")
    if is_repeated_sequence(norm):
        raise ValueError("CNPJ não pode ser sequência repetida (ex: 'AAAAAAAAAAAAAA').")
    if not CNPJ_REGEX.fullmatch(norm):
        raise ValueError(
            "Formato de CNPJ inválido (deve ser alfanumérico, maiúsculo, 14 caracteres)."
        )
    for c in norm[:12]:
        if c in FORBIDDEN_LETTERS:
            raise ValueError(f"CNPJ contém letra proibida: '{c}'.")
    base, dv = norm[:12], norm[12:]
    if calculate_cnpj_dvs(base) != dv:
        raise ValueError("Dígitos verificadores do CNPJ inválidos.")
    return norm


CNPJStr = Annotated[str, AfterValidator(cnpj_validator)]
