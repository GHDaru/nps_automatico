from enum import Enum
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, Required, NotRequired
import operator as op

from langgraph.types import Send
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse.langchain import CallbackHandler
from langgraph.graph import StateGraph, START, END


from dotenv import load_dotenv

from pathlib import Path

class TipoAvaliacao(str, Enum):
    ComunicacaoClareza = "Comunicação e Clareza"
    ProfissionalismoConformidade = "Profissionalismo e Conformidade"
    ResolucaoEficiencia = "Resolução e Eficiência"


class ResultadoAnalise(BaseModel):
    nota: int = Field(description="Nota baseada em evidências do chat", ge=0, le=100)
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


def abrir_system_prompt(titulo: str) -> str:
    """
    Le o prompt de sistema a partir da pasta de prompts.
    Parametros:
        titulo: Nome do arquivo de prompt (string)
    Retorna:
        Conteudo do arquivo de prompt (string)
    """
    base_dir: Path = Path(__file__).resolve().parents[0]
    caminho: Path =  base_dir / "src" / "app" / "prompts" / "system" / f"{titulo}.md"

    if not caminho.exists():
        raise Exception(f"O caminho '{str(caminho)}' não existe!")

    with open(str(caminho), "r", encoding="utf-8") as arquivo:
        resultado: str = arquivo.read()

    return resultado


def abrir_txt(src: str) -> str:
    """
    Le um arquivo de texto e retorna seu conteudo.
    Parametros:
        src: Caminho do arquivo (string)
    Retorna:
        Conteudo do arquivo (string)
    """
    src_path: Path = Path(src)

    if not src_path.exists():
        raise Exception(f"Arquivo '{src}' não encontrado")

    with open(src, "r", encoding="utf-8") as arquivo:
        conteudo = arquivo.read()

    return conteudo

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
# langfuse_handler = CallbackHandler()


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
        # config={"callbacks": [langfuse_handler]},
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

    # return grafo.compile().with_config({"callbacks": [langfuse_handler]})
    return grafo.compile().with_config({"callbacks": []})


if __name__ == "__main__":
    dados = { "chat_avaliado": "vai a merda, desculpa, mas voce é um lixo",
            "avaliacoes":[]         
            }
    
    grafo = build_grafo()
    grafo.get_graph().draw_mermaid_png()

    # resultado = grafo.invoke(dados)
    # print(resultado)





