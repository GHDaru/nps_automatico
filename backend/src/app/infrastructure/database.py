import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

_DATABASE_URL: str | None = os.getenv("DATABASE_URL")


def _get_connection() -> psycopg2.extensions.connection:
    if not _DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não configurado. "
            "Adicione a variável DATABASE_URL ao arquivo .env"
        )
    return psycopg2.connect(_DATABASE_URL)


@contextmanager
def get_db():
    """Context manager que fornece uma conexão e faz commit/rollback automaticamente."""
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
