"""
Script para crear el primer usuario admin.

Uso: cd backend && uv run python scripts/create_admin.py

Lee variables del entorno:
- ADMIN_USERNAME (default: "admin")
- ADMIN_EMAIL (default: "admin@localhost")
- ADMIN_PASSWORD (default: "admin123")
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app.models import User
from app.services.auth_service import get_password_hash

# Configurar engine async
engine = create_async_engine(settings.database_url, echo=False)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def create_admin_user():
    """Crea el usuario admin si no existe."""
    username = os.getenv("ADMIN_USERNAME", "admin")
    email = os.getenv("ADMIN_EMAIL", "admin@localhost")
    password = os.getenv("ADMIN_PASSWORD", "admin123")

    # Crear tablas si no existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Crear sesión
    async with async_session() as session:
        # Verificar si el usuario ya existe
        result = await session.execute(
            select(User).where(User.username == username)
        )
        existing_user = result.scalars().first()

        if existing_user:
            print(f"❌ El usuario '{username}' ya existe.")
            return

        # Crear usuario admin
        hashed_password = get_password_hash(password)
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role="admin",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        session.add(admin_user)
        await session.commit()

        print(f"✅ Usuario admin creado exitosamente:")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Role: admin")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_admin_user())
