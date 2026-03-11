from ..domain.graph import (
    EstadoGeral,
    Avaliacao,
    TipoAvaliacao,
    ResultadoAnalise,
    ResultadoAvaliacao,
)
from ..utils.file import abrir_system_prompt, abrir_txt
from langgraph.types import Send
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler
from langgraph.graph import StateGraph, START, END


from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-5-mini", temperature=0.2)
langfuse_handler = CallbackHandler()


def entrada(state: EstadoGeral):
    """Entrada do fluxo, também distriu o chat entre diferents workers para avaliar diferentes pontos da conversa"""
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

    agente = create_agent(
        llm, system_prompt=system_prompt, response_format=ResultadoAnalise
    )

    response = agente.invoke(
        {"messages": [{"role": "user", "content": state["chat"]}]},
        config={"callbacks": [langfuse_handler]},
    )
    response_formated: ResultadoAnalise = response["structured_response"]

    return {
        "avaliacoes": [
            {
                "nota": response_formated.nota,
                "justificativa": response_formated.justificativa,
                "tipo_avaliacao": state["tipo_avaliacao"],
            }
        ]
    }


def retornar_resultado(state: EstadoGeral):
    """Retorna os resultados da analise"""
    return {"avaliacoes": state["avaliacoes"]}


def build_grafo():
    """
    Monta e compila o grafo de execucao das avaliacoes.
    Parametros:
        nenhum
    Retorna:
        Grafo compilado com callbacks configurados
    """
    grafo = StateGraph(EstadoGeral)

    # Adicionar vertices
    grafo.add_node("entrada", entrada)
    grafo.add_node("avaliar", avaliar)
    grafo.add_node("retornar_resultado", retornar_resultado)

    # Adicionar arestas
    grafo.add_conditional_edges(START, entrada, ["avaliar"])
    grafo.add_edge("avaliar", "retornar_resultado")
    grafo.add_edge("retornar_resultado", END)

    return grafo.compile().with_config({"callbacks": [langfuse_handler]})
