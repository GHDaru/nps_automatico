from pydantic import BaseModel, Field
from datetime import datetime
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


# ── Prompt models ──────────────────────────────────────────────────────────────

class PromptCreate(BaseModel):
    nome: str = Field(description="Nome da dimensão de análise")
    conteudo: str = Field(description="Conteúdo completo do prompt (instruções para o LLM)")
    ativo: bool = Field(default=True, description="Indica se o prompt está ativo para o fluxo de avaliação")


class PromptUpdate(BaseModel):
    nome: str | None = None
    conteudo: str | None = None
    ativo: bool | None = None


class PromptResponse(BaseModel):
    id: str
    nome: str
    conteudo: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime


# ── Campo Extraído models ──────────────────────────────────────────────────────

class CampoCreate(BaseModel):
    nome: str = Field(description="Nome do campo a ser extraído (ex: cliente, atendente)")
    descricao: str = Field(description="Descrição do campo para ser exportada no JSON")


class CampoUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None


class CampoResponse(BaseModel):
    id: str
    nome: str
    descricao: str
    criado_em: datetime
    atualizado_em: datetime

