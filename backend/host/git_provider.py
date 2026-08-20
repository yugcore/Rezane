"""Git status provider for local workspace introspection."""
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class GitFileEntry(BaseModel):
    path: str
    status: str  # "modified", "untracked", "staged", "deleted"
    badge: str   # "M", "??", "A", "D"

class GitStatusSummary(BaseModel):
    is_git: bool
    repository: str = "RezaneAI"
    remote_url: str = "https://github.com/yugcore"
    branch: str = "main"
    ahead: int = 0
    behind: int = 0
    modified: List[GitFileEntry] = Field(default_factory=list)
    untracked: List[GitFileEntry] = Field(default_factory=list)
    staged: List[GitFileEntry] = Field(default_factory=list)
    additions: int = 0
    deletions: int = 0

class GitProvider:
    """Provides repository metadata and diff state for the dashboard."""

    def get_status(self, repo_path: Optional[str] = None) -> GitStatusSummary:
        cwd = Path(repo_path or ".").resolve()
        
        # Check if git repo
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode != 0:
                return GitStatusSummary(is_git=False)
            
            repo_root = Path(res.stdout.strip())
            repo_name = repo_root.name
        except Exception:
            return GitStatusSummary(is_git=False)

        # Get remote URL
        remote_url = "https://github.com/yugcore"
        remote_res = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False
        )
        if remote_res.returncode == 0 and remote_res.stdout.strip():
            remote_url = remote_res.stdout.strip()

        # Get branch
        branch = "main"
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False
        )
        if branch_res.returncode == 0:
            branch = branch_res.stdout.strip()

        # Get ahead/behind
        ahead, behind = 0, 0
        ab_res = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False
        )
        if ab_res.returncode == 0:
            parts = ab_res.stdout.strip().split()
            if len(parts) >= 2:
                behind = int(parts[0])
                ahead = int(parts[1])

        # Get file status
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False
        )
        
        modified_list = []
        untracked_list = []
        staged_list = []

        if status_res.returncode == 0:
            for line in status_res.stdout.splitlines():
                if len(line) < 4:
                    continue
                x = line[0]
                y = line[1]
                file_rel = line[3:].strip()

                if x in ("M", "A", "D", "R"):
                    staged_list.append(GitFileEntry(path=file_rel, status="staged", badge=x))
                if y == "M":
                    modified_list.append(GitFileEntry(path=file_rel, status="modified", badge="M"))
                elif x == "?" and y == "?":
                    untracked_list.append(GitFileEntry(path=file_rel, status="untracked", badge="??"))
                elif y == "D":
                    modified_list.append(GitFileEntry(path=file_rel, status="deleted", badge="D"))

        # Diff shortstat
        diff_res = subprocess.run(
            ["git", "diff", "--shortstat"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False
        )
        additions, deletions = 0, 0
        if diff_res.returncode == 0 and diff_res.stdout:
            text = diff_res.stdout.strip()
            import re
            ins_match = re.search(r'(\d+)\s+insertion', text)
            del_match = re.search(r'(\d+)\s+deletion', text)
            if ins_match:
                additions = int(ins_match.group(1))
            if del_match:
                deletions = int(del_match.group(1))

        return GitStatusSummary(
            is_git=True,
            repository=repo_name,
            remote_url=remote_url,
            branch=branch,
            ahead=ahead,
            behind=behind,
            modified=modified_list,
            untracked=untracked_list,
            staged=staged_list,
            additions=additions,
            deletions=deletions
        )

git_provider = GitProvider()
