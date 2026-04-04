"""
Configuración de pytest para SysMho Hunter.
Aislamiento total de base de datos usando setup sincrónico y tests asíncronos.
"""

import os
import pytest
import asyncio
import asyncpg
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from app.database.connection import db as db_singleton

load_dotenv()

# Configuración de base de datos de PRUEBAS
TEST_DB_NAME = "sysmho_test"
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "ander123")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")

def setup_test_db():
    """Crea la base de datos de prueba de forma sincrónica."""
    conn = psycopg2.connect(
        user=DB_USER, password=DB_PASS, host=DB_HOST, database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    cursor.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    cursor.close()
    conn.close()

    # Cargar esquema
    conn = psycopg2.connect(
        user=DB_USER, password=DB_PASS, host=DB_HOST, database=TEST_DB_NAME
    )
    cursor = conn.cursor()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sql_files = [
        "database/01_types.sql",
        "database/02_tables.sql",
        "database/03_functions.sql",
        "database/04_triggers.sql",
        "database/05_init_data.sql"
    ]
    for sql_file in sql_files:
        with open(os.path.join(project_root, sql_file), 'r') as f:
            cursor.execute(f.read())
    conn.commit()
    cursor.close()
    conn.close()

@pytest.fixture(scope="session", autouse=True)
def db_setup():
    """Fixture de sesión que prepara la base de datos una sola vez."""
    setup_test_db()
    yield
    # Opcional: Limpiar al final si se desea

@pytest.fixture
async def db():
    """Fixture de función que provee una conexión asyncpg limpia."""
    conn = await asyncpg.connect(
        user=DB_USER, password=DB_PASS, host=DB_HOST, database=TEST_DB_NAME
    )
    # Usamos una transacción por test para limpieza automática
    tx = conn.transaction()
    await tx.start()
    try:
        yield conn
    finally:
        await tx.rollback()
        await conn.close()

@pytest.fixture(scope="function", autouse=True)
async def init_singleton(db_setup):
    """Inicializa el pool de base de datos para los repositorios."""
    # Obtenemos el pool de asyncpg de forma similar a como lo hace el backend
    pool = await asyncpg.create_pool(
        user=DB_USER, password=DB_PASS, host=DB_HOST, database=TEST_DB_NAME,
        min_size=1, max_size=5
    )
    db_singleton._pool = pool
    yield
    await pool.close()
    db_singleton._pool = None
