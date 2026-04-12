"""
conftest.py — Fixtures globales para todos los tests de SysMho Hunter.

BD de tests: sysmho_hunter_test (PostgreSQL real, no mock).
Cada test recibe una sesión que se revierte al finalizar (rollback),
dejando la BD limpia para el siguiente test.
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Agregar backend/ al sys.path para que 'app' sea importable
# desde cualquier directorio donde se lance pytest
_BACKEND = Path(__file__).parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# ── Apuntar a BD de tests antes de importar la app ───────────────────
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:ander123@127.0.0.1/sysmho_hunter_test",
)
os.environ.setdefault("TEST_DATABASE_URL", TEST_DB_URL)

# Parchar settings ANTES de que la app los lea
os.environ["DB_NAME"] = "sysmho_hunter_test"

from app.database import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.models.action import PendingAction  # noqa: E402
from app.models.scan import Scan  # noqa: E402
from app.models.target import Scope, Target  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.auth_service import get_password_hash  # noqa: E402

# ── Engine de tests ──────────────────────────────────────────────────
# NullPool: cada operación crea su propia conexión física.
# Evita el InterfaceError de asyncpg por conexiones compartidas entre fixtures.
test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Event loop único para toda la sesión de pytest ───────────────────
@pytest.fixture(scope="session")
def event_loop():
    """Reutilizar un solo event loop en todos los tests async."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Crear / destruir tablas una vez por sesión ───────────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Crea las tablas al inicio y las elimina al terminar."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Sesión de BD por test (con limpieza post-test) ───────────────────
@pytest_asyncio.fixture
async def db() -> AsyncSession:
    """
    Sesión async estándar. Después de cada test se borran todos los datos
    (DELETE en orden inverso de FK) → BD limpia para el siguiente test.

    asyncpg no soporta bien transacciones anidadas para rollback,
    así que usamos cleanup explícito.
    """
    async with TestSessionLocal() as session:
        yield session

    # Cleanup: TRUNCATE CASCADE respeta FK automáticamente
    async with TestSessionLocal() as session:
        table_names = ", ".join(
            t.name for t in Base.metadata.sorted_tables
        )
        await session.execute(
            text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")
        )
        await session.commit()


# ── Override de dependencia get_session en la app ────────────────────
@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncClient:
    """
    Cliente HTTP async que usa la sesión de test.
    Sobreescribe get_session para que FastAPI use la BD de test.
    """
    from app.database import get_session

    async def override_get_session():
        yield db

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Fixtures de datos ────────────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """Usuario admin listo para usar en tests."""
    user = User(
        id=uuid.uuid4(),
        username="anderson_test",
        email="anderson@test.local",
        hashed_password=get_password_hash("testpass123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, admin_user: User) -> dict:
    """
    Headers de autenticación JWT listos para usar.
    Hace login real y extrae el access_token.
    """
    response = await client.post(
        "/auth/login",
        json={"username": admin_user.username, "password": "testpass123"},
    )
    assert response.status_code == 200, (
        f"Login falló: {response.text}"
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_target(db: AsyncSession) -> Target:
    """Target de prueba con un scope de dominio."""
    target = Target(
        id=uuid.uuid4(),
        name="Test Program",
        organization="TestCorp",
        h1_program_slug="testcorp",
        status="active",
        priority=5,
    )
    db.add(target)
    await db.flush()

    scope = Scope(
        id=uuid.uuid4(),
        target_id=target.id,
        scope_type="domain",
        value="testcorp.com",
        is_in_scope=True,
    )
    db.add(scope)
    await db.flush()

    return target


@pytest_asyncio.fixture
async def sample_scan(db: AsyncSession, sample_target: Target) -> Scan:
    """Scan en estado 'pending' asociado al target de prueba."""
    scan = Scan(
        id=uuid.uuid4(),
        target_id=sample_target.id,
        scan_type="recon",
        status="pending",
    )
    db.add(scan)
    await db.flush()
    return scan


@pytest_asyncio.fixture
async def pending_action(
    db: AsyncSession,
    sample_target: Target,
    sample_scan: Scan,
) -> PendingAction:
    """PendingAction en estado 'pending' para tests de aprobación."""
    action = PendingAction(
        id=uuid.uuid4(),
        action_type="command_approval",
        description="Ejecutar subfinder contra testcorp.com",
        target_id=sample_target.id,
        scan_id=sample_scan.id,
        payload={
            "tool_name": "subfinder",
            "command": "subfinder -d testcorp.com -silent",
            "human_explanation": "Buscar subdominios.",
            "why_needed": "Mapear superficie de ataque.",
            "risk_explanation": "Riesgo muy bajo.",
        },
        risk_level="low",
        risk_reason="Solo consulta DNS público.",
        requested_by="agent",
        status="pending",
    )
    db.add(action)
    await db.flush()
    return action
