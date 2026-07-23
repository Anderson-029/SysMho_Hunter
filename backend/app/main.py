"""
SysMho Hunter v0.2.0 — Backend FastAPI.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.brain import router as brain_router
from app.api.v1.router import router as api_router
from app.config import settings
from app.database import engine
from app.security import auth_middleware
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

    # Verificar LLM local (OpenAI-compatible)
    from app.brain.local_llm import local_llm

    if await local_llm.is_available():
        print(f"✅ Local LLM disponible ({settings.local_llm_model})")
    else:
        print(
            "⚠️  Local LLM no disponible — cerebro usará nivel 3 (cloud)"
        )

    yield

    # Shutdown
    await engine.dispose()
    print("🔴 Backend detenido.")


app = FastAPI(
    title="SysMho Hunter",
    description="Agente autónomo de Pentesting — HackerOne",
    version="0.2.0",
    lifespan=lifespan,
    # Docs deshabilitados en producción
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# =====================================================================
# Middleware: trailing slash solo en rutas auth que lo requieren
# =====================================================================
# No reescribir rutas OpenAPI sin slash (p.ej. /api/v1/brain/status)
# — eso provoca 307 en bucle con redirect_slashes de Starlette.
_TRAILING_SLASH_PATHS = {
    "/auth/login",
    "/auth/refresh",
    "/auth/logout",
}


async def normalize_trailing_slash(request, call_next):
    """Añade trailing slash solo a rutas auth canónicas sin slash."""
    if request.method in ("GET", "POST", "DELETE", "PATCH"):
        path = request.url.path
        if path in _TRAILING_SLASH_PATHS:
            request.scope["path"] = path + "/"
    return await call_next(request)


app.middleware("http")(normalize_trailing_slash)

# Middleware de autenticación dual (API Key OR JWT)
app.middleware("http")(auth_middleware)

# CORS — solo frontend autorizado
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

app.include_router(auth_router)
app.include_router(brain_router, prefix="/api/v1")
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
        "local_llm": "available"
        if await local_llm.is_available()
        else "unavailable",
    }
