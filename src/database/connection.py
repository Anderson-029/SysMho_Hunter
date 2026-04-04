"""
SysMho Hunter - Pool de conexiones a PostgreSQL.

Gestiona el pool de conexiones asíncronas a la base de datos
usando asyncpg para máximo rendimiento.
"""

import os
from typing import Any, Optional

import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Configuración de conexión desde variables de entorno
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "ander123"),
    "database": os.getenv("DB_NAME", "sysmho_hunter"),
}


class DatabasePool:
    """Singleton del pool de conexiones PostgreSQL."""

    _instance: Optional["DatabasePool"] = None
    _pool: Optional[asyncpg.Pool] = None

    def __new__(cls) -> "DatabasePool":
        """Garantiza una sola instancia del pool."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        """Inicializa el pool de conexiones."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                min_size=2,
                max_size=10,
                **DB_CONFIG,
            )

    async def close(self) -> None:
        """Cierra el pool de conexiones."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    @property
    def pool(self) -> asyncpg.Pool:
        """Retorna el pool activo."""
        if self._pool is None:
            raise RuntimeError(
                "El pool de base de datos no ha sido inicializado. "
                "Llama a initialize() primero."
            )
        return self._pool

    async def fetch_one(
        self, query: str, *args: Any
    ) -> Optional[asyncpg.Record]:
        """Ejecuta una consulta y retorna un solo registro."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetch_all(
        self, query: str, *args: Any
    ) -> list[asyncpg.Record]:
        """Ejecuta una consulta y retorna todos los registros."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetch_val(
        self, query: str, *args: Any
    ) -> Any:
        """Ejecuta una consulta y retorna un solo valor."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute(
        self, query: str, *args: Any
    ) -> str:
        """Ejecuta una consulta sin retorno de datos."""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)


# Instancia global
db = DatabasePool()
