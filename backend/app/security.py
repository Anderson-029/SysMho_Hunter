"""
Seguridad — API Key authentication y middleware.
"""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """Verifica que el API Key sea válido.

    Raise HTTPException 403 si es inválido o falta.
    """
    if not api_key:
        raise HTTPException(
            status_code=403, detail="Missing X-API-Key header"
        )

    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key


async def api_key_middleware(request: Request, call_next):
    """Middleware que verifica API key en TODOS los endpoints.

    Excepciones:
    - /health — para health checks
    - /docs, /redoc, /openapi.json — documentación (deshabilitada en prod)
    """
    # Endpoints que NO requieren API key
    public_paths = ["/health"]

    if request.url.path in public_paths:
        return await call_next(request)

    # Obtener header
    api_key = request.headers.get("X-API-Key")

    if not api_key or api_key != settings.api_key:
        return JSONResponse(
            status_code=403, content={"detail": "Invalid or missing API key"}
        )

    return await call_next(request)
