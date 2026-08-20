"""Tool Definition and Registry."""
import inspect
from typing import Callable, Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..permissions.engine import PermissionLevel

class ToolDefinition(BaseModel):
    name: str
    description: str
    permission_level: PermissionLevel
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)
    
    # Exclude handler from JSON serialization
    class Config:
        arbitrary_types_allowed = True

class ToolRegistry:
    """Central catalog of available assistant tools."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        permission_level: PermissionLevel,
        description: str = ""
    ):
        def decorator(func: Callable):
            sig = inspect.signature(func)
            params = {}
            for p_name, param in sig.parameters.items():
                params[p_name] = {
                    "type": str(param.annotation) if param.annotation != inspect._empty else "Any",
                    "default": None if param.default == inspect._empty else param.default,
                    "required": param.default == inspect._empty
                }
            
            tool_def = ToolDefinition(
                name=name,
                description=description or (func.__doc__ or "").strip(),
                permission_level=permission_level,
                parameters_schema=params
            )
            self._tools[name] = tool_def
            self._handlers[name] = func
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def get_handler(self, name: str) -> Optional[Callable]:
        return self._handlers.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

tool_registry = ToolRegistry()
register_tool = tool_registry.register
