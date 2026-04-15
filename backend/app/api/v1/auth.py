"""
Endpoints de autenticación — login, refresh, logout, me.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserMe,
)
from app.security import get_current_user, hash_token
from app.services.auth_service import (
    authenticate_user,
    create_tokens,
    logout_user,
    refresh_access_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login/", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Login con username y password.

    Retorna access_token y refresh_token si las credenciales son válidas.
    """
    # Autenticar usuario
    user = await authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Crear tokens
    tokens = await create_tokens(user)

    # Guardar refresh token hash en la BD
    user.refresh_token_hash = hash_token(tokens["refresh_token"])
    user.last_login = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()

    return TokenResponse(**tokens)


@router.post("/refresh/", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Refresh del access token usando un refresh token válido.

    Retorna nuevo access_token si el refresh_token es válido.
    """
    result = await refresh_access_token(db, request.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return TokenResponse(**result)


@router.post("/logout/")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Logout del usuario actual.

    Invalida el refresh token, por lo que no se pueden generar
    nuevos access tokens.
    """
    await logout_user(db, current_user)
    return {"detail": "Logged out successfully"}


@router.get("/me", response_model=UserMe)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserMe:
    """Obtiene información del usuario actual."""
    return UserMe(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
    )
