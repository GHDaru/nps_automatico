import atexit
import os
import signal
import sys
from psycopg_pool import ConnectionPool
from typing import Union, Optional
import threading

DATABASE_URL: str = f"postgresql://{os.environ['PG_USER']}:{os.environ['PG_PASSWORD']}@{os.environ['PG_HOST']}:{os.environ['PG_PORT']}/{os.environ['PG_DB']}"
_pool: Optional[ConnectionPool] = None
_lock: threading.Lock = threading.Lock()


def get_pool() -> ConnectionPool:
    """
    Obtem (ou inicializa) o pool de conexoes PostgreSQL.
    Parametros:
        nenhum
    Retorna:
        Instancia de ConnectionPool pronta para uso
    """
    global _pool
    if _pool is None:
        with _lock:
            if _pool is None:
                _pool = ConnectionPool(
                    conninfo=DATABASE_URL, min_size=1, max_size=30, open=True
                )
    return _pool


def shutdown_pool():
    """
    Encerra o pool de conexoes, se ativo.
    Parametros:
        nenhum
    Retorna:
        nada
    """
    if _pool is not None:
        _pool.close(timeout=5.0)


# Garante fechamento no shutdown
atexit.register(shutdown_pool)
signal.signal(signal.SIGTERM, lambda s, f: shutdown_pool() or sys.exit(0))
signal.signal(signal.SIGINT, lambda s, f: shutdown_pool() or sys.exit(0))
