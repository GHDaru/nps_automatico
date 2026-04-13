from ..domain.graph import ResultadoAvaliacao, TipoAvaliacao
from ..domain.models import ResultadoFinal, DimensoesPersonalizadas
from ..config import grafo
from ..infrastructure.nodes import avaliar_com_instrucoes
import statistics


class InputDadosController:
    @staticmethod
    def processar_chat(chat: str) -> ResultadoFinal:
        """Chama o grafo, realiza a computação e retorna o resultado"""
        resultado = grafo.invoke({"chat_avaliado": chat, "avaliacoes": []})
        avaliacoes: list[ResultadoAvaliacao] = resultado["avaliacoes"]

        apenas_notas = [item["nota"] for item in avaliacoes]

        media = sum(apenas_notas) / len(apenas_notas)
        mediana = statistics.median(apenas_notas)

        return ResultadoFinal(
            avaliacoes=avaliacoes, nota_media=media, nota_mediana=mediana
        )

    @staticmethod
    def processar_chat_personalizado(
        chat: str, dimensoes: DimensoesPersonalizadas
    ) -> ResultadoFinal:
        """Chama cada dimensão com as instruções personalizadas e retorna o resultado"""
        mapeamento = [
            (TipoAvaliacao.ComunicacaoClareza, dimensoes.comunicacao),
            (TipoAvaliacao.ProfissionalismoConformidade, dimensoes.profissionalismo),
            (TipoAvaliacao.ResolucaoEficiencia, dimensoes.resolucao),
        ]

        avaliacoes: list[ResultadoAvaliacao] = [
            avaliar_com_instrucoes(chat, tipo, instrucoes)
            for tipo, instrucoes in mapeamento
        ]

        apenas_notas = [item["nota"] for item in avaliacoes]
        media = sum(apenas_notas) / len(apenas_notas)
        mediana = statistics.median(apenas_notas)

        return ResultadoFinal(
            avaliacoes=avaliacoes, nota_media=media, nota_mediana=mediana
        )
