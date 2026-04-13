from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.input_dados import router as input_dados_router
from .routes.prompts import router as prompts_router
from .routes.campos import router as campos_router
from .routes.metadados import router as metadados_router

# FastAPI
app = FastAPI()
app.include_router(input_dados_router)
app.include_router(prompts_router)
app.include_router(campos_router)
app.include_router(metadados_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
