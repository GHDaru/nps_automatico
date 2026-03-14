import traceback
from uuid import UUID

import psycopg2.extras
from fastapi import APIRouter, HTTPException

from ...domain.models import CampoCreate, CampoResponse, CampoUpdate
from ...infrastructure.database import get_db

router = APIRouter(prefix="/campos", tags=["campos"])


def _row_to_campo(row: dict) -> CampoResponse:
    return CampoResponse(
        id=str(row["id"]),
        nome=row["nome"],
        descricao=row["descricao"],
        criado_em=row["criado_em"],
        atualizado_em=row["atualizado_em"],
    )


@router.get("", response_model=list[CampoResponse])
def listar_campos():
    """Retorna todos os campos extraídos cadastrados."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM campos_extraidos ORDER BY nome")
                rows = cur.fetchall()
        return [_row_to_campo(r) for r in rows]
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.post("", response_model=CampoResponse, status_code=201)
def criar_campo(body: CampoCreate):
    """Cria um novo campo extraído."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO campos_extraidos (nome, descricao)
                    VALUES (%s, %s)
                    RETURNING *
                    """,
                    (body.nome, body.descricao),
                )
                row = cur.fetchone()
        return _row_to_campo(row)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        if "unique" in str(exc).lower():
            raise HTTPException(
                status_code=409, detail=f"Já existe um campo com o nome '{body.nome}'"
            )
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.get("/{campo_id}", response_model=CampoResponse)
def obter_campo(campo_id: UUID):
    """Retorna um campo extraído pelo ID."""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM campos_extraidos WHERE id = %s", (str(campo_id),)
                )
                row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Campo não encontrado")
        return _row_to_campo(row)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.put("/{campo_id}", response_model=CampoResponse)
def atualizar_campo(campo_id: UUID, body: CampoUpdate):
    """Atualiza um campo extraído existente (apenas os campos fornecidos)."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="Nenhum campo para atualizar")

    set_clause = ", ".join(f"{col} = %s" for col in updates)
    values = list(updates.values()) + [str(campo_id)]

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"UPDATE campos_extraidos SET {set_clause} WHERE id = %s RETURNING *",
                    values,
                )
                row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Campo não encontrado")
        return _row_to_campo(row)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        if "unique" in str(exc).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Já existe um campo com o nome '{updates.get('nome')}'",
            )
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.delete("/{campo_id}", status_code=204)
def deletar_campo(campo_id: UUID):
    """Remove um campo extraído pelo ID."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM campos_extraidos WHERE id = %s RETURNING id",
                    (str(campo_id),),
                )
                deleted = cur.fetchone()
        if deleted is None:
            raise HTTPException(status_code=404, detail="Campo não encontrado")
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())
