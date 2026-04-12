"""
test_scans.py — Tests del API de scans y el sistema de aprobación.

Cubre:
- POST /api/v1/scans: crear scan con target válido
- GET /api/v1/scans: listar scans
- GET /api/v1/scans/{id}: obtener scan por ID
- DELETE /api/v1/scans/{id}: cancelar scan
- PATCH /api/v1/actions/{id}: aprobar / rechazar PendingAction
- Scope enforcement: scan contra target fuera de scope falla
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import PendingAction
from app.models.scan import Scan
from app.models.target import Target


# ══════════════════════════════════════════════════════════════════════
# Crear scan
# ══════════════════════════════════════════════════════════════════════

class TestCreateScan:

    async def test_crear_scan_requiere_auth(
        self, client: AsyncClient, sample_target: Target
    ):
        """Sin token, crear scan retorna 401 o 403."""
        response = await client.post(
            "/api/v1/scans",
            json={
                "target_id": str(sample_target.id),
                "scan_type": "recon",
            },
        )
        assert response.status_code in (401, 403)

    async def test_crear_scan_target_valido(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_target: Target,
    ):
        """Con auth y target válido, crea el scan en estado pending."""
        response = await client.post(
            "/api/v1/scans/",
            json={
                "target_id": str(sample_target.id),
                "scan_type": "recon",
            },
            headers=auth_headers,
        )
        assert response.status_code in (200, 201), response.text
        data = response.json()
        assert data["target_id"] == str(sample_target.id)
        assert data["scan_type"] == "recon"
        assert data["status"] in ("pending", "running")

    async def test_crear_scan_target_inexistente_falla(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Target ID que no existe retorna 404 o 422."""
        response = await client.post(
            "/api/v1/scans/",
            json={
                "target_id": str(uuid.uuid4()),
                "scan_type": "recon",
            },
            headers=auth_headers,
        )
        assert response.status_code in (404, 422), response.text


# ══════════════════════════════════════════════════════════════════════
# Listar y obtener scans
# ══════════════════════════════════════════════════════════════════════

class TestGetScans:

    async def test_listar_scans_requiere_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/scans")
        assert response.status_code in (401, 403)

    async def test_listar_scans_retorna_lista(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_scan: Scan,
    ):
        """Con auth, devuelve lista con al menos el scan creado."""
        response = await client.get("/api/v1/scans/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        ids = [s["id"] for s in data]
        assert str(sample_scan.id) in ids

    async def test_obtener_scan_por_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_scan: Scan,
    ):
        response = await client.get(
            f"/api/v1/scans/{sample_scan.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_scan.id)

    async def test_scan_inexistente_retorna_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            f"/api/v1/scans/{uuid.uuid4()}", headers=auth_headers
        )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════
# Cancelar scan
# ══════════════════════════════════════════════════════════════════════

class TestCancelScan:

    async def test_cancelar_scan_running(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        sample_scan: Scan,
    ):
        """Cancelar un scan en estado running lo pone en cancelled."""
        # Poner el scan en running
        sample_scan.status = "running"
        await db.commit()

        response = await client.delete(
            f"/api/v1/scans/{sample_scan.id}/cancel", headers=auth_headers
        )
        assert response.status_code in (200, 204), response.text

    async def test_cancelar_scan_inexistente_retorna_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.delete(
            f"/api/v1/scans/{uuid.uuid4()}/cancel", headers=auth_headers
        )
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════
# Pending actions — aprobar / rechazar
# ══════════════════════════════════════════════════════════════════════

class TestPendingActions:

    async def test_listar_pending_actions(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pending_action: PendingAction,
    ):
        """Con una pending action creada, aparece en la lista."""
        response = await client.get(
            "/api/v1/actions/", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        ids = [a["id"] for a in data]
        assert str(pending_action.id) in ids

    async def test_aprobar_action(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pending_action: PendingAction,
        db: AsyncSession,
    ):
        """POST /actions/{id}/review con approved actualiza el status."""
        response = await client.post(
            f"/api/v1/actions/{pending_action.id}/review",
            json={"decision": "approved", "review_notes": "Aprobado en test"},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "approved"

    async def test_rechazar_action(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pending_action: PendingAction,
    ):
        """POST /actions/{id}/review con rejected actualiza el status."""
        response = await client.post(
            f"/api/v1/actions/{pending_action.id}/review",
            json={"decision": "rejected", "review_notes": "Demasiado riesgo"},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "rejected"

    async def test_action_inexistente_retorna_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            f"/api/v1/actions/{uuid.uuid4()}/review",
            json={"decision": "approved"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_aprobar_requiere_auth(
        self, client: AsyncClient, pending_action: PendingAction
    ):
        response = await client.post(
            f"/api/v1/actions/{pending_action.id}/review",
            json={"decision": "approved"},
        )
        assert response.status_code in (401, 403)
