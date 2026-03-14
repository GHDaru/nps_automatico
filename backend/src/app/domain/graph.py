from enum import Enum
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, Required, NotRequired
import operator as op


class TipoAvaliacao(str, Enum):
    ComunicacaoClareza = "Comunicação e Clareza"
    ProfissionalismoConformidade = "Profissionalismo e Conformidade"
    ResolucaoEficiencia = "Resolução e Eficiência"


class ResultadoAnalise(BaseModel):
    nota: int = Field(description="Nota baseada em evidências do chat", ge=0, le=10)
    justificativa: str = Field(
        description="Justificativa detalhada baseada em evidências do chat referenciando trechos da conversa"
    )


class Avaliacao(TypedDict):
    chat: str
    tipo_avaliacao: TipoAvaliacao


class ResultadoAvaliacao(TypedDict):
    nota: Required[int]
    justificativa: Required[str]
    tipo_avaliacao: NotRequired[TipoAvaliacao]


class EstadoGeral(TypedDict):
    chat_avaliado: Required[str]
    avaliacoes: Required[Annotated[list[ResultadoAvaliacao], op.add]]
    erros: NotRequired[Annotated[list[str], op.add]]
    tipo_avaliacao: NotRequired[TipoAvaliacao]
