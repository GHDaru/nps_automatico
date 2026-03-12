import uuid
from typing import Any, Sequence, Optional
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from .connection import get_pool
from ...domain.graph import ResultadoAvaliacao
from ...domain.models import Task
from psycopg_pool import ConnectionPool


def inserir_avaliacao_completa(
    cnpj: str,
    chat: str,
    detalhes: list[ResultadoAvaliacao],
    lote_id: Optional[uuid.UUID] = None,
) -> Optional[dict[str, Any]]:
    """
    Insere uma avaliação completa chamando a função PL/pgSQL inserir_avaliacao_completa.
    Parâmetros:
        cnpj: CNPJ da empresa (string)
        chat: Texto do chat avaliado (string)
        detalhes: Lista de dicts {"criterio": str, "nota": int, "justificativa": str}
        lote_id: UUID do lote (opcional, pode ser None)
    Retorna:
        dict com os campos: id (UUID), cnpj (str), media (float), mediana (float), detalhes (list)
    """
    pool = get_pool()
    with (
        pool.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
    ):
        cur.execute(
            "SELECT inserir_avaliacao_completa(%s, %s, %s, %s)",
            (cnpj, chat, Jsonb(detalhes), lote_id),
        )
        resultado = cur.fetchone()
    return resultado


def criar_lote(cnpj: str, num_total_itens: int) -> uuid.UUID:
    """
    Chama a funcao SQL para criar um lote de avaliacoes.
    Parametros:
        cnpj: CNPJ da empresa (string)
        num_total_itens: Numero total de itens no lote (int)
    Retorna:
        UUID do lote criado
    """
    pool = get_pool()
    with (
        pool.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
    ):
        cur.execute("SELECT criar_lote(%s, %s, %s)", (cnpj, num_total_itens, 0))
        id_ = cur.fetchone()

    return id_["criar_lote"]  # type: ignore


def criar_avaliacao_pendente(cnpj: str, id_: uuid.UUID, chat: str) -> uuid.UUID:
    """
    Insere uma avaliacao pendente vinculada a um lote.
    Parametros:
        cnpj: CNPJ da empresa (string)
        id_: UUID do lote (uuid.UUID)
        chat: Texto do chat avaliado (string)
    Retorna:
        UUID da avaliacao pendente criada
    """
    pool = get_pool()
    with (
        pool.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
    ):
        cur.execute(
            "INSERT INTO avaliacoes (cnpj, lote_id, chat, status) VALUES (%s, %s, %s, 'pending') RETURNING id",
            (cnpj, id_, chat),
        )
        retorno = cur.fetchone()  # type: ignore
    return retorno["id"]  # type: ignore


def atualizar_avaliacao(task: Task, vereditos: list[ResultadoAvaliacao]) -> None:
    pool = get_pool()
    with (
        pool.connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
    ):
        cur.execute(
            "UPDATE avaliacoes SET status='done' WHERE id = %s",
            [str(task["avaliacao_id"])],
        )

        cur.executemany(
            "INSERT INTO detalhes_avaliacao (avaliacao_id, criterio, nota, justificativa) VALUES (%s, %s, %s, %s)",
            [
                (
                    task["avaliacao_id"],
                    veredito["tipo_avaliacao"],  # type: ignore
                    veredito["nota"],
                    veredito["justificativa"],
                )
                for veredito in vereditos
            ],
        )
