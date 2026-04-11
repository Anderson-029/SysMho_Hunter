"""
Servicio de autenticación — lógica de negocio para login, refresh, logout.
"""

from datetime import datetime, timezone
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)

# Context de argon2 para hashing de passwords (más robusto que bcrypt)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que el plain password coincida con el hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera un hash bcrypt del password."""
    return pwd_context.hash(password)


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    """Autentica un usuario verificando username y password.

    Retorna el User si las credenciales son válidas, None en caso contrario.
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalars().first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


async def create_tokens(user: User) -> dict:
    """Crea access_token y refresh_token para un usuario.

    Retorna dict con:
    - access_token: str
    - refresh_token: str
    - token_type: str ("bearer")
    - expires_in: int (segundos)
    """
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": (
            settings.access_token_expire_minutes * 60
        ),  # Convertir a segundos
    }


async def refresh_access_token(
    db: AsyncSession, refresh_token: str
) -> dict | None:
    """Genera un nuevo access_token a partir de un refresh_token válido.

    Verifica:
    1. El refresh_token es válido y no expirado
    2. El hash del token coincide con el guardado en la BD
    3. El usuario existe y está activo

    Retorna dict con nuevo access_token si todo es válido,
    None en caso contrario.
    """
    try:
        payload = decode_token(refresh_token)
    except Exception:
        return None

    # Verificar que es refresh token
    if payload.get("type") != "refresh":
        return None

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return None

    # Obtener usuario
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()

    if not user or not user.is_active:
        return None

    # Verificar que el hash del token coincida
    token_hash = hash_token(refresh_token)
    if user.refresh_token_hash != token_hash:
        return None

    # Generar nuevo access token (sin cambiar refresh token)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


async def logout_user(db: AsyncSession, user: User) -> None:
    """Invalida el refresh token del usuario (logout).

    Limpia el refresh_token_hash en la BD, lo que hace que el refresh_token
    ya no sea válido para obtener nuevos access tokens.
    """
    user.refresh_token_hash = None
    db.add(user)
    await db.commit()


async def get_user_by_id(
    db: AsyncSession, user_id: UUID
) -> User | None:
    """Obtiene un usuario por su ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalars().first()


async def update_last_login(
    db: AsyncSession, user: User
) -> None:
    """Actualiza el timestamp de último login del usuario."""
    user.last_login = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()
