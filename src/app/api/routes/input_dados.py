from typing import Union

from fastapi import APIRouter
from ...domain.models import (
    EntradaAvaliacaoSingular,
    MultiplasEntrada,
    ResultadoFinal,
    SaidaIntermediaria,
)
from ...domain.graph import ResultadoAvaliacao
from fastapi import FastAPI, Query, HTTPException
import numpy as np
from ...config import grafo
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
        entrada: Payload com CNPJ e chat (EntradaAvaliacaoSingular)
    Retorna:
        ResultadoFinal com avaliacoes, media e mediana
    """
    try:
        return InputDadosController.processar_chat(entrada.cnpj, entrada.chat)
    except Exception:
        raise HTTPException(status_code=502, detail=str(traceback.format_exc()))


@router.post("/lotes")
def realizar_avaliacao_em_massa(entrada: MultiplasEntrada) -> SaidaIntermediaria:
    """
    Cria um lote de avaliacoes e retorna o status inicial.
    Parametros:
        entrada: Payload com CNPJ e lista de chats (MultiplasEntrada)
    Retorna:
        SaidaIntermediaria com id do lote e contagem inicial
    """
    try:
        id_ = InputDadosController.criar_lote(entrada.cnpj, entrada.chats)
        return SaidaIntermediaria(
            lote_id=id_,
            total_itens=len(entrada.chats),
            completed_itens=0,
            resultados_prontos=[],
        )
    except Exception:
        raise HTTPException(status_code=502, detail=str(traceback.format_exc()))
