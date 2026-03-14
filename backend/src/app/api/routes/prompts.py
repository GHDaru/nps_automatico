import traceback
from uuid import UUID

import psycopg2.extras
from fastapi import APIRouter, HTTPException

from ...domain.models import PromptCreate, PromptResponse, PromptUpdate
from ...infrastructure.database import get_db

router = APIRouter(prefix="/prompts", tags=["prompts"])


def _row_to_prompt(row: dict) -> PromptResponse:
    return PromptResponse(
        id=str(row["id"]),
        nome=row["nome"],
        conteudo=row["conteudo"],
        ativo=row["ativo"],
        criado_em=row["criado_em"],
        atualizado_em=row["atualizado_em"],
    )


@router.get("", response_model=list[PromptResponse])
def listar_prompts():
    """Retorna todos os prompts cadastrados, ordenados pelo nome."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM prompts ORDER BY nome")
                rows = cur.fetchall()
        return [_row_to_prompt(r) for r in rows]
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.post("", response_model=PromptResponse, status_code=201)
def criar_prompt(body: PromptCreate):
    """Cria um novo prompt."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO prompts (nome, conteudo, ativo)
                    VALUES (%s, %s, %s)
                    RETURNING *
                    """,
                    (body.nome, body.conteudo, body.ativo),
                )
                row = cur.fetchone()
        return _row_to_prompt(row)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.get("/{prompt_id}", response_model=PromptResponse)
def obter_prompt(prompt_id: UUID):
    """Retorna um prompt pelo ID."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM prompts WHERE id = %s", (str(prompt_id),))
                row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Prompt não encontrado")
        return _row_to_prompt(row)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.put("/{prompt_id}", response_model=PromptResponse)
def atualizar_prompt(prompt_id: UUID, body: PromptUpdate):
    """Atualiza um prompt existente (apenas os campos fornecidos)."""
    _ALLOWED_COLS = {"nome", "conteudo", "ativo"}
    updates = {
        k: v for k, v in body.model_dump().items()
        if v is not None and k in _ALLOWED_COLS
    }
    if not updates:
        raise HTTPException(status_code=422, detail="Nenhum campo para atualizar")

    set_clause = ", ".join(f"{col} = %s" for col in updates)
    values = list(updates.values()) + [str(prompt_id)]

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"UPDATE prompts SET {set_clause} WHERE id = %s RETURNING *",
                    values,
                )
                row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Prompt não encontrado")
        return _row_to_prompt(row)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.delete("/{prompt_id}", status_code=204)
def deletar_prompt(prompt_id: UUID):
    """Remove um prompt pelo ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM prompts WHERE id = %s RETURNING id",
                    (str(prompt_id),),
                )
                deleted = cur.fetchone()
        if deleted is None:
            raise HTTPException(status_code=404, detail="Prompt não encontrado")
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())
