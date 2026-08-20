"""Git Tools implementation."""
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from ..permissions.engine import PermissionLevel
from .registry import register_tool

def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False
    )

@register_tool("git_status", PermissionLevel.LEVEL_0_READ_ONLY, "Get the current branch and working tree status of a Git repository.")
async def git_status(repo_path: Optional[str] = None) -> Dict[str, Any]:
    cwd = Path(repo_path or ".").resolve()
    
    # Check branch
    branch_res = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if branch_res.returncode != 0:
        return {"status": "error", "error": "Not a git repository or git not found"}
    
    branch = branch_res.stdout.strip()
    
    # Check ahead/behind
    ahead_behind_res = _run_git(["rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"], cwd)
    ahead, behind = 0, 0
    if ahead_behind_res.returncode == 0:
        parts = ahead_behind_res.stdout.strip().split()
        if len(parts) >= 2:
            behind, ahead = int(parts[0]), int(parts[1])

    # Status porcelain
    status_res = _run_git(["status", "--porcelain"], cwd)
    modified = []
    untracked = []
    staged = []
    
    for line in status_res.stdout.splitlines():
        if not line:
            continue
        index_status = line[0]
        worktree_status = line[1]
        file_path = line[3:].strip()
        
        if index_status in ("M", "A", "D", "R"):
            staged.append(file_path)
        if worktree_status == "M":
            modified.append(file_path)
        elif index_status == "?" or worktree_status == "?":
            untracked.append(file_path)
            
    return {
        "status": "success",
        "repository": cwd.name,
        "branch": branch,
        "ahead": ahead,
        "behind": behind,
        "modified": modified,
        "untracked": untracked,
        "staged": staged,
        "has_changes": bool(modified or untracked or staged)
    }

@register_tool("git_stage_all", PermissionLevel.LEVEL_1_LOW_RISK, "Stage all modified and untracked files.")
async def git_stage_all(repo_path: Optional[str] = None) -> Dict[str, Any]:
    cwd = Path(repo_path or ".").resolve()
    res = _run_git(["add", "."], cwd)
    if res.returncode == 0:
        return {"status": "success", "message": "All files staged successfully"}
    return {"status": "error", "error": res.stderr}

@register_tool("git_commit", PermissionLevel.LEVEL_2_DESTRUCTIVE, "Commit staged changes with a commit message.")
async def git_commit(message: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
    cwd = Path(repo_path or ".").resolve()
    res = _run_git(["commit", "-m", message], cwd)
    if res.returncode == 0:
        return {"status": "success", "message": res.stdout.strip()}
    return {"status": "error", "error": res.stderr or res.stdout}
