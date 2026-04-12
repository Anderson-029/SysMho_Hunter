"""
WebSocket para stream de logs en tiempo real.
El frontend se conecta a /ws/live?token=<jwt> para recibir AgentLog.
"""

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.log import AgentLog
from app.security import decode_token

router = APIRouter()

# Conjunto de conexiones activas
_connections: set[WebSocket] = set()


async def _send_to_all(message: str) -> None:
    """Envía un mensaje a todos los clientes conectados."""
    disconnected = set()
    for ws in _connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)
    _connections.difference_update(disconnected)


async def broadcast_log(log: AgentLog) -> None:
    """Enviar un log a todos los clientes WebSocket conectados."""
    message = json.dumps(
        {
            "id": str(log.id),
            "scan_id": str(log.scan_id) if log.scan_id else None,
            "log_level": log.log_level,
            "component": log.component,
            "message": log.message,
            "created_at": log.created_at.isoformat()
            if log.created_at
            else None,
        }
    )
    await _send_to_all(message)


async def broadcast_command_request(action: object) -> None:
    """Notifica al frontend que hay un comando esperando aprobación.

    Emite evento tipo 'command_request' con toda la info para el modal.
    """
    payload = getattr(action, "payload", {}) or {}
    message = json.dumps(
        {
            "type": "command_request",
            "action_id": str(action.id),
            "tool_name": payload.get("tool_name", ""),
            "command": payload.get("command", ""),
            "human_explanation": payload.get("human_explanation", ""),
            "why_needed": payload.get("why_needed", ""),
            "risk_explanation": payload.get("risk_explanation", ""),
            "risk_level": action.risk_level,
            "scan_id": str(action.scan_id) if action.scan_id else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    await _send_to_all(message)


async def broadcast_command_output(
    tool_name: str, raw_output: str, scan_id: str | None = None
) -> None:
    """Transmite el output de un comando al terminal del frontend."""
    lines = [line for line in raw_output.splitlines() if line.strip()][:100]
    message = json.dumps(
        {
            "type": "command_output",
            "tool_name": tool_name,
            "scan_id": scan_id,
            "lines": lines,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    await _send_to_all(message)


@router.websocket("/live")
async def websocket_live(websocket: WebSocket):
    # Extraer token del query param
    token = websocket.query_params.get("token")
    api_key = websocket.headers.get("X-API-Key")

    # Validar autenticación
    auth_ok = False

    # Opción 1: JWT token en query param
    if token:
        try:
            payload = decode_token(token)
            if payload.get("type") == "access":
                auth_ok = True
        except Exception:
            pass

    # Opción 2: API Key en header
    if not auth_ok and api_key == settings.api_key:
        auth_ok = True

    if not auth_ok:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized"
        )
        return

    await websocket.accept()
    _connections.add(websocket)
    try:
        # Enviar los últimos 20 logs al conectarse
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentLog).order_by(AgentLog.created_at.desc()).limit(20)
            )
            recent = list(reversed(result.scalars().all()))
            for log in recent:
                await broadcast_log(log)

        # Mantener la conexión activa
        while True:
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        _connections.discard(websocket)
    except Exception:
        _connections.discard(websocket)
