"""
SysMho Hunter v0.2.0 — Backend FastAPI.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router
from app.config import settings
from app.database import engine
from app.websocket.router import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("✅ SysMho Hunter backend iniciando...")

    # Cargar modelos ML
    from app.brain.ml_engine import ml_engine

    if ml_engine.load():
        print("✅ Modelos ML cargados")
    else:
        print(
            "⚠️  Modelos ML no disponibles"
            " (ejecuta: uv run python ml/training/train_models.py)"
        )

    # Verificar Ollama
    from app.brain.local_llm import local_llm

    if await local_llm.is_available():
        print(f"✅ Ollama disponible ({settings.ollama_model})")
    else:
        print("⚠️  Ollama no disponible — cerebro usará nivel 3 (cloud)")

    yield

    # Shutdown
    await engine.dispose()
    print("🔴 Backend detenido.")


app = FastAPI(
    title="SysMho Hunter",
    description="Agente autónomo de Pentesting Web y Bug Bounty — HackerOne",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws")


@app.get("/health")
async def health_check() -> dict:
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    from app.brain.local_llm import local_llm
    from app.brain.ml_engine import ml_engine

    return {
        "status": "online",
        "version": "0.2.0",
        "database": db_status,
        "ml_engine": "loaded" if ml_engine.is_available else "unavailable",
        "ollama": "available"
        if await local_llm.is_available()
        else "unavailable",
    }
