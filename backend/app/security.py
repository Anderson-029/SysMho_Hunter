"""
Seguridad — JWT authentication, API Key backward compatibility, middleware.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.database import get_session
from app.models import User

# =====================================================================
# Esquemas de seguridad
# =====================================================================

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# =====================================================================
# Utilidades JWT
# =====================================================================


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Crea un JWT access token con los datos provistos."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Crea un JWT refresh token con expiración de 7 días."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decodifica y valida un JWT.

    Lanza JWTError si el token es inválido, expirado o de tipo incorrecto.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def hash_token(token: str) -> str:
    """Genera un hash SHA-256 para almacenamiento seguro."""
    return hashlib.sha256(token.encode()).hexdigest()


# =====================================================================
# Dependencies de FastAPI
# =====================================================================


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Obtiene el usuario actual del JWT access token.

    Lanza HTTPException 401 si el token es inválido, expirado
    o el usuario no existe.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exception

    token_type = payload.get("type")
    if token_type != "access":
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    from uuid import UUID

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception

    # Consultar usuario en BD
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalars().first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verifica que el usuario actual sea admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_operator(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verifica que el usuario actual sea admin u operator."""
    if current_user.role not in ("admin", "operator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator access required",
        )
    return current_user


# =====================================================================
# Middleware dual: API Key OR JWT
# =====================================================================


async def auth_middleware(request: Request, call_next):
    """Middleware que valida API Key (backward compat) O JWT.

    Rutas públicas (no requieren autenticación):
    - /health
    - /auth/login, /auth/refresh
    - /docs, /redoc, /openapi.json

    Para otras rutas:
    1. Si header X-API-Key válido → autorizado
    2. Si header Authorization: Bearer <token> válido → autorizado
    3. Si es OPTIONS (CORS preflight) → autorizado
    4. Sino → 401 Unauthorized
    """
    # Rutas públicas (patrones base, sin trailing slash)
    public_prefixes = {
        "/health",
        "/auth/login",
        "/auth/refresh",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/brain/status",
        "/api/v1/brain/test",
        "/api/v1/brain/stats",
    }

    # CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    # Chequear si es ruta pública (con o sin trailing slash)
    request_path = request.url.path
    is_public = any(
        request_path == path or request_path == path + "/"
        for path in public_prefixes
    )
    if is_public:
        return await call_next(request)

    # Obtener headers
    api_key = request.headers.get("X-API-Key")
    auth_header = request.headers.get("Authorization", "")

    # Verificar API Key (backward compatibility)
    if api_key and api_key == settings.api_key:
        return await call_next(request)

    # Verificar JWT (Bearer token)
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]  # "Bearer " = 7 caracteres
        try:
            payload = decode_token(token)
            if payload.get("type") == "access":
                return await call_next(request)
        except JWTError:
            pass  # Token inválido, continuar

    # Si ninguno válido → 401
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Not authenticated"},
    )
