"""WebSocket Event Bus for real-time bi-directional telemetry."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Set
from fastapi import WebSocket
from pydantic import BaseModel, Field

logger = logging.getLogger("rezane.events")

class AssistantEvent(BaseModel):
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EventBus:
    """Manages active WebSocket connections and broadcasts typed events."""
    
    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
            logger.info(f"WebSocket client connected. Total clients: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self._connections)}")

    async def broadcast(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Broadcasts an event to all connected WebSocket clients."""
        event = AssistantEvent(event_type=event_type, payload=payload)
        message_str = event.model_dump_json()
        
        async with self._lock:
            if not self._connections:
                return
            
            stale_connections = []
            for ws in self._connections:
                try:
                    await ws.send_text(message_str)
                except Exception as ex:
                    logger.warning(f"Error sending to WebSocket client: {ex}")
                    stale_connections.append(ws)
            
            for ws in stale_connections:
                self._connections.discard(ws)

    def publish_nowait(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Helper to broadcast without awaiting directly from sync or background tasks."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(event_type, payload))
        except RuntimeError:
            pass

event_bus = EventBus()
