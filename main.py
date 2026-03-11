from src.app.api import app
from uvicorn import run
from src.app.infrastructure.db.db_access import criar_lote, criar_avaliacao_pendente

if __name__ == "__main__":
    run(app=app, host="localhost", port=5020)
    # id_ = criar_lote("M4.N7P.2S6/X3Y9-70", 20)
    # id_2 = criar_avaliacao_pendente("M4.N7P.2S6/X3Y9-70", id_, "TESTE")

    # print(f"ID LOTE: {id_}")
    # print(f"ID AVALIACAO: {id_2}")
