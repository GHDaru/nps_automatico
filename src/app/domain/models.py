from pydantic import BaseModel, Field, field_validator
from .graph import ResultadoAvaliacao
from ..utils.validacoes import cnpj_validator, CNPJStr
import re, uuid
from typing import TypedDict


class EntradaAvaliacaoSingular(BaseModel):
    chat: str = Field(
        description="Campo onde deve ficar o chat/chamado por completo e organizado de cima para baixo em ordem crescente em relação ao timestamp do momento em que a mensagem foi enviada, e organiar também por ATENDENTE e CLIENTE por fins de organização e dar a nomeclatura correta para um dos atores participantes do chat/chamado"
    )
    cnpj: CNPJStr = Field(
        description="Campo para guardar o CNPJ da empresa que está tendo seu chat avaliado"
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


class MultiplasEntrada(BaseModel):
    chats: list[str] = Field(
        description="Processamento de multiplos chamados em paralelo"
    )
    cnpj: CNPJStr = Field(
        description="Campo para guardar o CNPJ da empresa que está tendo seus chats avaliados"
    )


class MultiplasSaidas(BaseModel):
    resultados: list[ResultadoFinal] = Field(
        description="Retorno de inumeros resultados processados paralelamente"
    )


class SaidaIntermediaria(BaseModel):
    lote_id: uuid.UUID = Field(description="Identificar da tarefa pendente")
    total_itens: int = Field(
        description="Lista o total de processos enviados para serem processados"
    )
    completed_itens: int = Field(
        description="Retorna o numero de tarefas completadas com sucesso"
    )
    resultados_prontos: list[ResultadoFinal]


class Task(TypedDict):
    avaliacao_id: uuid.UUID
    cnpj: CNPJStr
    lote_id: uuid.UUID
    chat: str
