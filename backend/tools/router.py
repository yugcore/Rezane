"""Tool Router for dispatching calls with permission checking and logging."""
import time
import inspect
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from .registry import tool_registry
from ..permissions.engine import permission_engine
from ..events.event_bus import event_bus

logger = logging.getLogger("rezane.tools.router")

class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    requires_confirmation: bool = False

class ToolRouter:
    """Dispatches tool calls safely with permission checks and telemetry."""

    async def execute(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        user_confirmed: bool = False
    ) -> ToolExecutionResult:
        parameters = parameters or {}
        tool_def = tool_registry.get_tool(tool_name)
        
        if not tool_def:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' not found in registry."
            )

        # Permission check
        perm_check = permission_engine.check_permission(
            tool_name=tool_name,
            tool_level=tool_def.permission_level,
            parameters=parameters,
            user_confirmed=user_confirmed
        )

        if not perm_check.allowed:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                requires_confirmation=perm_check.requires_confirmation,
                error=perm_check.message
            )

        handler = tool_registry.get_handler(tool_name)
        if not handler:
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"No handler registered for '{tool_name}'."
            )

        start_time = time.perf_counter()
        
        # Broadcast tool start event
        await event_bus.broadcast("tool_start", {
            "tool_name": tool_name,
            "parameters": parameters,
            "level": tool_def.permission_level.value
        })

        try:
            if inspect.iscoroutinefunction(handler):
                result_data = await handler(**parameters)
            else:
                result_data = handler(**parameters)
                
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Broadcast tool completion
            await event_bus.broadcast("tool_complete", {
                "tool_name": tool_name,
                "success": True,
                "elapsed_ms": elapsed_ms
            })

            return ToolExecutionResult(
                tool_name=tool_name,
                success=True,
                data=result_data,
                execution_time_ms=elapsed_ms
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(f"Error executing tool {tool_name}")
            
            await event_bus.broadcast("tool_error", {
                "tool_name": tool_name,
                "error": str(e),
                "elapsed_ms": elapsed_ms
            })

            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                execution_time_ms=elapsed_ms
            )

tool_router = ToolRouter()
