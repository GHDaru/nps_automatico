from fastapi import APIRouter, HTTPException
from ...domain.models import EntradaAvaliacaoSingular, EntradaAvaliacaoPersonalizada, ResultadoFinal
from ...controllers.input_dados import InputDadosController
import traceback

router = APIRouter(prefix="/chamados")


@router.post("/avaliacao_individual")
def realizar_avaliacao_individual(
    entrada: EntradaAvaliacaoSingular,
) -> ResultadoFinal:
    """
    Processa um unico chat e retorna a avaliacao final.
    Parametros:
        entrada: Payload com chat (EntradaAvaliacaoSingular)
    Retorna:
        ResultadoFinal com avaliacoes, media e mediana
    """
    try:
        return InputDadosController.processar_chat(entrada.chat)
    except Exception:
        raise HTTPException(status_code=502, detail=str(traceback.format_exc()))


@router.post("/avaliacao_individual_personalizada")
def realizar_avaliacao_individual_personalizada(
    entrada: EntradaAvaliacaoPersonalizada,
) -> ResultadoFinal:
    """
    Processa um unico chat com instruções personalizadas por dimensão e retorna a avaliacao final.
    Parametros:
        entrada: Payload com chat e dimensoes (EntradaAvaliacaoPersonalizada)
    Retorna:
        ResultadoFinal com avaliacoes, media e mediana
    """
    try:
        return InputDadosController.processar_chat_personalizado(
            entrada.chat, entrada.dimensoes
        )
    except Exception:
        raise HTTPException(status_code=502, detail=str(traceback.format_exc()))
