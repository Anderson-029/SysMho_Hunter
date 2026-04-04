"""
SysMho Hunter - WebSocket para comunicación en tiempo real.

Permite al frontend recibir logs, pensamientos del agente
y hallazgos en tiempo real mientras un escaneo está activo.
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Gestor de conexiones WebSocket activas."""

    def __init__(self) -> None:
        """Inicializa el gestor de conexiones."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Acepta y registra una nueva conexión WebSocket."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Elimina una conexión WebSocket del registro."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        """Envía un mensaje a todas las conexiones activas."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(
        self, websocket: WebSocket, message: dict
    ) -> None:
        """Envía un mensaje a una conexión específica."""
        await websocket.send_json(message)


# Instancia global del gestor de conexiones
manager = ConnectionManager()


@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Endpoint WebSocket para streaming de eventos del agente."""
    await manager.connect(websocket)
    try:
        # Mensaje de bienvenida
        await manager.send_personal(websocket, {
            "type": "system",
            "data": {
                "message": "Conectado a SysMho Hunter",
                "status": "ready",
            },
        })
        while True:
            # Escuchar comandos del frontend
            data = await websocket.receive_text()
            command = json.loads(data)
            await handle_ws_command(websocket, command)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def handle_ws_command(
    websocket: WebSocket, command: dict
) -> None:
    """Procesa comandos recibidos desde el frontend vía WebSocket."""
    cmd_type = command.get("type", "")

    if cmd_type == "ping":
        await manager.send_personal(websocket, {
            "type": "pong",
            "data": {"timestamp": command.get("timestamp")},
        })
    elif cmd_type == "subscribe_scan":
        scan_id = command.get("scan_id")
        await manager.send_personal(websocket, {
            "type": "subscribed",
            "data": {"scan_id": scan_id},
        })
    else:
        await manager.send_personal(websocket, {
            "type": "error",
            "data": {"message": f"Comando desconocido: {cmd_type}"},
        })
