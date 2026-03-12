from typing import Any, Callable
from uuid import UUID
import msgpack
from ...domain.models import Task


def encode_uuid(obj: Any) -> Any:
    """Função pura para serializar UUIDs como strings."""
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Tipo não serializável: {type(obj)}")


def decode_task(dct: dict[str, Any]) -> dict[str, Any]:
    """Função pura para desserializar campos UUID do Task."""
    uuid_fields = {"avaliacao_id", "lote_id"}
    for field in uuid_fields:
        if field in dct and isinstance(dct[field], str):
            try:
                dct[field] = UUID(dct[field])
            except ValueError:
                pass  # Campo não é UUID válido, mantém como string
    return dct


def pack_task(task: Task) -> bytes:
    """Serializa Task para bytes usando msgpack."""
    return msgpack.packb(task, default=encode_uuid, use_bin_type=True)


def unpack_task(data: bytes) -> Task:
    """Desserializa bytes para Task usando msgpack."""
    return msgpack.unpackb(data, object_hook=decode_task, raw=False)
