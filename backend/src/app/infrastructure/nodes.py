from ..domain.graph import (
    EstadoGeral,
    Avaliacao,
    TipoAvaliacao,
    ResultadoAnalise,
    ResultadoAvaliacao,
)
from ..utils.file import abrir_system_prompt
from langgraph.types import Send
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

# Langfuse é opcional: só ativa se as chaves estiverem configuradas
_callbacks: list = []
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    try:
        from langfuse.langchain import CallbackHandler

        _callbacks = [CallbackHandler()]
    except Exception:
        pass


def entrada(state: EstadoGeral):
    """Entrada do fluxo, distribui o chat entre diferentes workers para avaliar diferentes pontos da conversa"""
    return [
        Send("avaliar", {"chat": state["chat_avaliado"], "tipo_avaliacao": i})
        for i in [
            TipoAvaliacao.ComunicacaoClareza,
            TipoAvaliacao.ProfissionalismoConformidade,
            TipoAvaliacao.ResolucaoEficiencia,
        ]
    ]


def avaliar(state: Avaliacao):
    """Avalia uma determinada conversa em relação ao tipo de avaliação definida"""
    match state["tipo_avaliacao"]:
        case TipoAvaliacao.ComunicacaoClareza:
            system_prompt = abrir_system_prompt("Comunicação e Clareza")
        case TipoAvaliacao.ProfissionalismoConformidade:
            system_prompt = abrir_system_prompt("Profissionalismo e Conformidade")
        case TipoAvaliacao.ResolucaoEficiencia:
            system_prompt = abrir_system_prompt("Resolução e Eficiência")
        case _:
            raise Exception("Fora dos padrões")

    structured_llm = llm.with_structured_output(ResultadoAnalise)
    response: ResultadoAnalise = structured_llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state["chat"]},
        ],
        config={"callbacks": _callbacks} if _callbacks else {},
    )

    return {
        "avaliacoes": [
            {
                "nota": response.nota,
                "justificativa": response.justificativa,
                "tipo_avaliacao": state["tipo_avaliacao"],
            }
        ]
    }


def build_grafo():
    """
    Monta e compila o grafo de execucao das avaliacoes.
    Parametros:
        nenhum
    Retorna:
        Grafo compilado (com callbacks de observabilidade se configurados)
    """
    grafo = StateGraph(EstadoGeral)

    # Adicionar vertices
    grafo.add_node("entrada", entrada)
    grafo.add_node("avaliar", avaliar)

    # Adicionar arestas
    grafo.add_conditional_edges(START, entrada, ["avaliar"])
    grafo.add_edge("avaliar", END)

    compiled = grafo.compile()
    if _callbacks:
        return compiled.with_config({"callbacks": _callbacks})
    return compiled
