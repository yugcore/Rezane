"""Tools package initialization."""
from .registry import tool_registry, register_tool, ToolDefinition
from .router import tool_router, ToolExecutionResult

# Import tool modules to ensure registration
from . import os_tools
from . import git_tools

__all__ = ["tool_registry", "register_tool", "ToolDefinition", "tool_router", "ToolExecutionResult"]
