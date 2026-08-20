"""Operating System Tools implementation."""
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import ImageGrab
from ..permissions.engine import PermissionLevel
from .registry import register_tool

@register_tool("open_application", PermissionLevel.LEVEL_1_LOW_RISK, "Launch a desktop application by name or path.")
async def open_application(name: str) -> Dict[str, Any]:
    name_lower = name.lower().strip()
    
    app_commands = {
        "vscode": ["code"],
        "vs code": ["code"],
        "visual studio code": ["code"],
        "terminal": ["wt.exe"],
        "powershell": ["powershell.exe"],
        "cmd": ["cmd.exe"],
        "notepad": ["notepad.exe"],
        "explorer": ["explorer.exe"],
        "file explorer": ["explorer.exe"],
        "calculator": ["calc.exe"],
        "godot": ["godot"],
        "unreal": ["UnrealEditor"]
    }

    cmd = app_commands.get(name_lower, [name])
    try:
        # Check if executable exists in PATH or is direct command
        subprocess.Popen(cmd, shell=True)
        return {"status": "success", "message": f"Launched application: {name}"}
    except Exception as e:
        # Fallback to os.startfile if Windows
        try:
            os.startfile(name)
            return {"status": "success", "message": f"Opened {name} via shell"}
        except Exception as err:
            return {"status": "error", "error": f"Failed to launch '{name}': {str(err)}"}

@register_tool("open_folder", PermissionLevel.LEVEL_1_LOW_RISK, "Open a local folder path in File Explorer.")
async def open_folder(path: str) -> Dict[str, Any]:
    target_path = Path(path).resolve()
    if not target_path.exists():
        return {"status": "error", "error": f"Path does not exist: {path}"}
    
    try:
        os.startfile(str(target_path))
        return {"status": "success", "message": f"Opened folder: {target_path}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@register_tool("read_clipboard", PermissionLevel.LEVEL_0_READ_ONLY, "Read current plain text from the system clipboard.")
async def read_clipboard() -> Dict[str, Any]:
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                return {"status": "success", "text": data}
            return {"status": "success", "text": None, "message": "No text in clipboard"}
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        return {"status": "error", "error": str(e)}

@register_tool("take_screenshot", PermissionLevel.LEVEL_0_READ_ONLY, "Capture the primary or active screen as an image.")
async def take_screenshot(save_path: Optional[str] = None) -> Dict[str, Any]:
    try:
        screenshot = ImageGrab.grab(all_screens=True)
        if not save_path:
            save_dir = Path("./screenshots")
            save_dir.mkdir(exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(save_dir / f"screenshot_{timestamp}.png")
        
        screenshot.save(save_path)
        return {"status": "success", "file_path": str(Path(save_path).resolve())}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@register_tool("run_command", PermissionLevel.LEVEL_1_LOW_RISK, "Execute a shell command in a working directory.")
async def run_command(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "status": "success",
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Command execution timed out (30s limit)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
