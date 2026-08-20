"""Tool Permission & Security Engine according to idea.md Section 14."""
from enum import IntEnum
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field

logger = logging.getLogger("rezane.permissions")

class PermissionLevel(IntEnum):
    LEVEL_0_READ_ONLY = 0       # No confirmation required (Read active windows, git status, clipboard, screenshots)
    LEVEL_1_LOW_RISK = 1        # Usually automatic (Open app, focus window, open folder)
    LEVEL_2_DESTRUCTIVE = 2     # Requires confirmation (Delete files, overwrite files, destructive git)
    LEVEL_3_HIGH_RISK = 3       # Always requires explicit authorization (Admin ops, disk operations)

class AuditEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tool_name: str
    level: PermissionLevel
    parameters: Dict[str, Any]
    approved: bool
    caller: str = "assistant"
    reason: Optional[str] = None

class PermissionCheckResult(BaseModel):
    allowed: bool
    requires_confirmation: bool = False
    level: PermissionLevel
    message: str

class PermissionEngine:
    """Evaluates whether an OS or developer tool call meets security requirements."""

    def __init__(self, auto_approve_level1: bool = True):
        self.auto_approve_level1 = auto_approve_level1
        self.audit_log: List[AuditEntry] = []

    def check_permission(
        self,
        tool_name: str,
        tool_level: PermissionLevel,
        parameters: Dict[str, Any],
        user_confirmed: bool = False
    ) -> PermissionCheckResult:
        if tool_level == PermissionLevel.LEVEL_0_READ_ONLY:
            self._log(tool_name, tool_level, parameters, True)
            return PermissionCheckResult(
                allowed=True,
                requires_confirmation=False,
                level=tool_level,
                message=f"Tool {tool_name} is read-only. Auto-approved."
            )
        
        if tool_level == PermissionLevel.LEVEL_1_LOW_RISK:
            if self.auto_approve_level1 or user_confirmed:
                self._log(tool_name, tool_level, parameters, True)
                return PermissionCheckResult(
                    allowed=True,
                    requires_confirmation=False,
                    level=tool_level,
                    message=f"Tool {tool_name} is low-risk. Approved."
                )
            else:
                return PermissionCheckResult(
                    allowed=False,
                    requires_confirmation=True,
                    level=tool_level,
                    message=f"Action '{tool_name}' requires user confirmation."
                )

        if tool_level in (PermissionLevel.LEVEL_2_DESTRUCTIVE, PermissionLevel.LEVEL_3_HIGH_RISK):
            if user_confirmed:
                self._log(tool_name, tool_level, parameters, True)
                return PermissionCheckResult(
                    allowed=True,
                    requires_confirmation=False,
                    level=tool_level,
                    message=f"Privileged tool {tool_name} confirmed by user."
                )
            else:
                self._log(tool_name, tool_level, parameters, False, reason="Pending confirmation")
                return PermissionCheckResult(
                    allowed=False,
                    requires_confirmation=True,
                    level=tool_level,
                    message=f"High risk action '{tool_name}' requires explicit user confirmation."
                )

        return PermissionCheckResult(
            allowed=False,
            requires_confirmation=True,
            level=tool_level,
            message="Unknown permission policy."
        )

    def _log(self, tool_name: str, level: PermissionLevel, params: Dict[str, Any], approved: bool, reason: Optional[str] = None):
        entry = AuditEntry(
            tool_name=tool_name,
            level=level,
            parameters=params,
            approved=approved,
            reason=reason
        )
        self.audit_log.append(entry)
        logger.info(f"Audit: {tool_name} (L{level.value}) Approved={approved} Reason={reason or 'OK'}")

permission_engine = PermissionEngine()
