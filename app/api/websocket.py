"""
SysMho Hunter - WebSocket Manager.
Gestión de comunicación en tiempo real en la nueva estructura app/.
"""

import json
from typing import List, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])

class ConnectionManager:
    """Gestor de múltiples conexiones WebSocket activas."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict) -> None:
        """Envía datos a todos los clientes conectados."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Se maneja desconexión silenciosa durante el broadcast
                pass

    async def send_personal(self, websocket: WebSocket, message: Dict) -> None:
        """Mensaje privado a un cliente específico."""
        await websocket.send_json(message)

manager = ConnectionManager()

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Endpoint principal de streaming de eventos."""
    await manager.connect(websocket)
    try:
        # Bienvenida
        await manager.send_personal(websocket, {
            "type": "system",
            "data": {"message": "Conectado al núcleo de SysMho Hunter", "status": "online"}
        })
        while True:
            data = await websocket.receive_text()
            # Opcional: manejar comandos entrantes aquí
    except WebSocketDisconnect:
        manager.disconnect(websocket)
