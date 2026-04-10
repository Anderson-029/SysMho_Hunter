"""
WebSocket para stream de logs en tiempo real.
El frontend se conecta a /ws/live para recibir AgentLog en tiempo real.
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.log import AgentLog

router = APIRouter()

# Conjunto de conexiones activas
_connections: set[WebSocket] = set()


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
    disconnected = set()
    for ws in _connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)
    _connections.difference_update(disconnected)


@router.websocket("/live")
async def websocket_live(websocket: WebSocket):
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
