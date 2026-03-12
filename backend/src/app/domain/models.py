from pydantic import BaseModel, Field
from .graph import ResultadoAvaliacao


class EntradaAvaliacaoSingular(BaseModel):
    chat: str = Field(
        description="Campo onde deve ficar o chat/chamado por completo e organizado de cima para baixo em ordem crescente em relação ao timestamp do momento em que a mensagem foi enviada, e organiar também por ATENDENTE e CLIENTE por fins de organização e dar a nomeclatura correta para um dos atores participantes do chat/chamado"
    )


class ResultadoFinal(BaseModel):
    avaliacoes: list[ResultadoAvaliacao] = Field(
        description="Lista das avaliações realizadas"
    )
    nota_media: float = Field(
        description="Media total da nota final referente as 3 avaliações realizadas"
    )
    nota_mediana: float = Field(description="Mediana das notas finais")


class Erro(BaseModel):
    error_message: str = Field(description="Erro gerado escrito por inteiro")
