from src.app.api import app
from uvicorn import run

if __name__ == "__main__":
    run(app=app, host="0.0.0.0", port=5020)
