from ..domain.graph import ResultadoAvaliacao
from ..domain.models import ResultadoFinal
from ..config import grafo
import statistics


class InputDadosController:
    @staticmethod
    def processar_chat(chat: str) -> ResultadoFinal:
        """Chama o grafo, realiza a computação e elimina a duplicação"""
        resultado = grafo.invoke({"chat_avaliado": chat, "avaliacoes": []})
        avaliacoes: list[ResultadoAvaliacao] = resultado["avaliacoes"][
            0 : len(resultado["avaliacoes"]) // 2
        ]

        apenas_notas = [item["nota"] for item in avaliacoes]

        media = sum(apenas_notas) / len(apenas_notas)
        mediana = statistics.median(apenas_notas)

        return ResultadoFinal(
            avaliacoes=avaliacoes, nota_media=media, nota_mediana=mediana
        )
