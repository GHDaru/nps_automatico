import traceback

from fastapi import APIRouter, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

from ...domain.models import EntradaExtrairMetadados, MetadadosAtendimento
from ...utils.file import abrir_system_prompt

load_dotenv()

router = APIRouter(prefix="/chamados", tags=["chamados"])

_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

_callbacks: list = []
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    try:
        from langfuse.langchain import CallbackHandler
        _callbacks = [CallbackHandler()]
    except Exception:
        pass


@router.post("/extrair_metadados", response_model=MetadadosAtendimento)
def extrair_metadados(entrada: EntradaExtrairMetadados) -> MetadadosAtendimento:
    """
    Extrai metadados estruturados de um texto de atendimento via LLM.
    Parâmetros:
        entrada: Payload com o texto do atendimento (EntradaExtrairMetadados)
    Retorna:
        MetadadosAtendimento com os campos extraídos
    """
    try:
        system_prompt = abrir_system_prompt("Extrair Metadados")
        structured_llm = _llm.with_structured_output(MetadadosAtendimento)
        resultado: MetadadosAtendimento = structured_llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": entrada.atendimento},
            ],
            config={"callbacks": _callbacks} if _callbacks else {},
        )
        return resultado
    except Exception:
        raise HTTPException(status_code=502, detail=str(traceback.format_exc()))
