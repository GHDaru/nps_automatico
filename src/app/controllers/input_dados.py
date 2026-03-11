from ..domain.graph import ResultadoAvaliacao

from ..domain.models import ResultadoFinal, Task
from ..config import grafo
import numpy as np
import pika, redis, json, uuid, os
from ..infrastructure.db.db_access import (
    inserir_avaliacao_completa,
    criar_lote,
    criar_avaliacao_pendente,
    atualizar_avaliacao,
)
from ..infrastructure.messenger.producer import send_task

redis_client = redis.Redis(host="localhost", port=6379, db=0)


class InputDadosController:
    @staticmethod
    def processar_chat(cnpj: str, chat: str) -> ResultadoFinal:
        """Chama o grafo, realiza a computação e elimina a duplicação"""
        resultado = grafo.invoke({"chat_avaliado": chat, "avaliacoes": []})
        avaliacoes: list[ResultadoAvaliacao] = resultado["avaliacoes"][
            0 : len(resultado["avaliacoes"]) // 2
        ]

        apenas_notas = list(map(lambda item: item["nota"], avaliacoes))

        media = sum(apenas_notas) / len(apenas_notas)
        mediana = np.median(apenas_notas)

        inserir_avaliacao_completa(cnpj, chat, avaliacoes)

        return ResultadoFinal(
            avaliacoes=avaliacoes, nota_media=media, nota_mediana=mediana
        )

    @staticmethod
    def criar_lote(cnpj: str, chats: list[str]) -> uuid.UUID:
        """
        Cria um lote e registra as avaliacoes pendentes no banco.
        Parametros:
            cnpj: CNPJ da empresa (string)
            chats: Lista de conversas a serem avaliadas (list[str])
        Retorna:
            UUID do lote criado
        """
        id_lote = criar_lote(cnpj, len(chats))

        for chat in chats:
            id_avaliacao = criar_avaliacao_pendente(cnpj, id_lote, chat)
            send_task(
                Task(avaliacao_id=id_avaliacao, chat=chat, cnpj=cnpj, lote_id=id_lote)
            )

        return id_lote

    @staticmethod
    def processar_mensagem(task: Task) -> None:
        resultado = grafo.invoke({"chat_avaliado": task["chat"], "avaliacoes": []})
        avaliacoes: list[ResultadoAvaliacao] = resultado["avaliacoes"][
            0 : len(resultado["avaliacoes"]) // 2
        ]

        atualizar_avaliacao(task, avaliacoes)
