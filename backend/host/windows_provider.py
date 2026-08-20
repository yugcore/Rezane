"""Native Windows OS Window Detection and Management Provider with ctypes and psutil support."""
import logging
import ctypes
import ctypes.wintypes
from typing import List, Optional
from pydantic import BaseModel
import psutil

logger = logging.getLogger("rezane.host.windows")

class ActiveWindow(BaseModel):
    hwnd: int
    title: str
    process_name: str
    process_path: Optional[str] = None
    category: str = "App"  # "Code", "Terminal", "Engine", "Browser", "App"
    is_active: bool = False

# Known GUI processes to detect if running in background session
KNOWN_GUI_PROCS = {
    "code.exe": ("Visual Studio Code", "Code"),
    "devenv.exe": ("Visual Studio", "Code"),
    "windowsterminal.exe": ("Windows Terminal", "Terminal"),
    "powershell.exe": ("PowerShell", "Terminal"),
    "cmd.exe": ("Command Prompt", "Terminal"),
    "explorer.exe": ("File Explorer", "App"),
    "godot.exe": ("Godot Engine", "Engine"),
    "godot.windows.editor.x86_64.console.exe": ("Godot Engine Console", "Engine"),
    "unrealeditor.exe": ("Unreal Editor", "Engine"),
    "chrome.exe": ("Google Chrome", "Browser"),
    "msedge.exe": ("Microsoft Edge", "Browser"),
    "firefox.exe": ("Firefox", "Browser"),
    "spotify.exe": ("Spotify", "App"),
    "notepad.exe": ("Notepad", "App")
}

class WindowsProvider:
    """Detects and interacts with Windows OS applications and windows."""

    def __init__(self):
        self.user32 = None
        try:
            self.user32 = ctypes.windll.user32
        except Exception as e:
            logger.warning(f"Could not load user32.dll: {e}")

    def _categorize(self, title: str, process_name: str) -> str:
        t = title.lower()
        p = process_name.lower()
        
        if "code" in p or "devenv" in p or "visual studio" in t:
            return "Code"
        if "wt" in p or "terminal" in p or "powershell" in p or "cmd" in p or "bash" in t:
            return "Terminal"
        if "unreal" in t or "unreal" in p or "godot" in t or "godot" in p or "unity" in p or "zegfx" in t:
            return "Engine"
        if "chrome" in p or "firefox" in p or "edge" in p or "msedge" in p or "brave" in p:
            return "Browser"
        return "App"

    def list_active_windows(self) -> List[ActiveWindow]:
        windows: List[ActiveWindow] = []

        if self.user32:
            try:
                active_hwnd = self.user32.GetForegroundWindow()
                EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
                
                def enum_cb(hwnd, lparam):
                    if self.user32.IsWindowVisible(hwnd):
                        length = self.user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            self.user32.GetWindowTextW(hwnd, buff, length + 1)
                            title = buff.value.strip()
                            
                            # Filter system shell artifacts
                            if title and title not in ("Program Manager", "Settings", "Windows Input Experience", "Task Switching"):
                                pid = ctypes.wintypes.DWORD()
                                self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                                pname, ppath = "", None
                                try:
                                    proc = psutil.Process(pid.value)
                                    pname = proc.name()
                                    ppath = proc.exe()
                                except Exception:
                                    pass

                                cat = self._categorize(title, pname)
                                windows.append(ActiveWindow(
                                    hwnd=hwnd,
                                    title=title,
                                    process_name=pname or "application",
                                    process_path=ppath,
                                    category=cat,
                                    is_active=(hwnd == active_hwnd)
                                ))
                    return True

                self.user32.EnumWindows(EnumWindowsProc(enum_cb), 0)
            except Exception as e:
                logger.debug(f"EnumWindows error: {e}")

        # Fallback to process scanning if EnumWindows returns no windows (e.g. headless/background terminal)
        if not windows:
            windows = self._fallback_list_processes()

        return windows

    def focus_window(self, hwnd: int) -> bool:
        if not self.user32:
            return False
        try:
            # SW_RESTORE = 9
            self.user32.ShowWindow(hwnd, 9)
            self.user32.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logger.error(f"Failed to focus window {hwnd}: {e}")
            return False

    def _fallback_list_processes(self) -> List[ActiveWindow]:
        procs: List[ActiveWindow] = []
        seen_names = set()

        for p in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                name = (p.info['name'] or '').lower()
                if name in KNOWN_GUI_PROCS and name not in seen_names:
                    seen_names.add(name)
                    display_name, category = KNOWN_GUI_PROCS[name]
                    procs.append(ActiveWindow(
                        hwnd=p.info['pid'],
                        title=f"{display_name} (Process PID {p.info['pid']})",
                        process_name=p.info['name'],
                        process_path=p.info.get('exe'),
                        category=category,
                        is_active=False
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return procs

windows_provider = WindowsProvider()
