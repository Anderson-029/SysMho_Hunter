"""
SysMho Hunter - Punto de entrada principal del backend.

Servidor FastAPI que expone la API REST y WebSocket
para comunicación en tiempo real con el frontend.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import router as api_router
from app.api.websocket import router as ws_router
from app.database.connection import db

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación."""
    # Startup: inicializar pool de base de datos
    await db.initialize()
    print("✅ Pool de base de datos inicializado")
    yield
    # Shutdown: cerrar pool
    await db.close()
    print("🔴 Pool de base de datos cerrado")


app = FastAPI(
    title="SysMho Hunter",
    description="Agente de IA para Pentesting Web y Bug Bounty",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS para permitir la comunicación con el frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas de la API
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws")


@app.get("/health")
async def health_check() -> dict:
    """Endpoint de salud del servidor."""
    # Verificar conexión a la BD
    try:
        result = await db.fetch_val("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "online",
        "agent": "SysMho Hunter v0.1.0",
        "database": db_status,
    }
