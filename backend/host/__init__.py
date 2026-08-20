"""Host platform integration package."""
from .windows_provider import windows_provider, ActiveWindow
from .git_provider import git_provider, GitStatusSummary

__all__ = ["windows_provider", "ActiveWindow", "git_provider", "GitStatusSummary"]
