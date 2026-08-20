"""Browser Manager for Rezane AI Desktop Assistant.

Provides proper browser/webview instances capable of directly navigating to
external URLs (e.g. YouTube, Google, GitHub, Docs) with genuine origin isolation,
persistent cookies, storage, and WebSocket address-bar synchronization.
"""
import os
import sys
import uuid
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from pydantic import BaseModel, Field

from backend.events.event_bus import event_bus

logger = logging.getLogger("rezane.browser")

# Persistent browser storage directory (cookies, session storage, localStorage, cache)
BROWSER_PROFILE_DIR = Path.home() / ".rezane" / "browser_profile"
BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)


class BrowserTab(BaseModel):
    id: str = Field(default_factory=lambda: f"tab-{uuid.uuid4().hex[:8]}")
    url: Optional[str] = None
    title: str = "New Tab"
    favicon: Optional[str] = None
    history: List[str] = Field(default_factory=list)
    history_idx: int = -1
    is_loading: bool = False
    can_go_back: bool = False
    can_go_forward: bool = False


class BrowserState(BaseModel):
    tabs: List[BrowserTab] = Field(default_factory=list)
    active_tab_id: str = ""
    profile_dir: str = str(BROWSER_PROFILE_DIR)
    native_view_active: bool = False


class BrowserManager:
    """Manages genuine browser navigation, state, and native webview lifecycle."""

    def __init__(self):
        self._lock = threading.Lock()
        self._tabs: Dict[str, BrowserTab] = {}
        self._active_tab_id: str = ""
        self._native_window = None
        self._native_thread: Optional[threading.Thread] = None

        # Create initial tab
        initial_tab = BrowserTab(id="tab-1", title="New Tab", url=None)
        self._tabs[initial_tab.id] = initial_tab
        self._active_tab_id = initial_tab.id

    def get_state(self) -> BrowserState:
        with self._lock:
            tabs_list = list(self._tabs.values())
            return BrowserState(
                tabs=tabs_list,
                active_tab_id=self._active_tab_id,
                profile_dir=str(BROWSER_PROFILE_DIR),
                native_view_active=self._native_window is not None
            )

    def get_active_tab(self) -> BrowserTab:
        with self._lock:
            return self._tabs.get(self._active_tab_id) or list(self._tabs.values())[0]

    def _normalize_url(self, raw_url: str) -> str:
        url = raw_url.strip()
        if not url:
            return "https://www.google.com"
        
        # Check if direct domain vs search query
        if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("about:"):
            if "." in url and " " not in url:
                url = f"https://{url}"
            else:
                from urllib.parse import quote_plus
                url = f"https://www.google.com/search?q={quote_plus(url)}"
        return url

    def _extract_title_hint(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            host = parsed.netloc.replace("www.", "")
            if "youtube.com" in host:
                return "YouTube"
            if "google.com" in host:
                return "Google"
            if "github.com" in host:
                return "GitHub"
            if host:
                return host
        except Exception:
            pass
        return "Browser View"

    def navigate(self, raw_url: str, tab_id: Optional[str] = None) -> BrowserTab:
        target_url = self._normalize_url(raw_url)
        title_hint = self._extract_title_hint(target_url)

        with self._lock:
            target_tab_id = tab_id or self._active_tab_id
            if target_tab_id not in self._tabs:
                target_tab_id = self._active_tab_id
            
            tab = self._tabs[target_tab_id]
            
            # History tracking
            if tab.history_idx == -1 or (tab.history and tab.history[tab.history_idx] != target_url):
                tab.history = tab.history[:tab.history_idx + 1]
                tab.history.append(target_url)
                tab.history_idx = len(tab.history) - 1

            tab.url = target_url
            tab.title = title_hint
            tab.is_loading = True
            tab.can_go_back = tab.history_idx > 0
            tab.can_go_forward = tab.history_idx < len(tab.history) - 1

        # Broadcast update over WebSocket
        self._broadcast_state()

        # Update native window if active
        if self._native_window:
            try:
                self._native_window.load_url(target_url)
            except Exception as e:
                logger.warning(f"Error loading URL in native webview: {e}")

        # Mark loading complete
        with self._lock:
            if target_tab_id in self._tabs:
                self._tabs[target_tab_id].is_loading = False

        self._broadcast_state()
        return self._tabs[target_tab_id]

    def go_back(self, tab_id: Optional[str] = None) -> BrowserTab:
        with self._lock:
            tid = tab_id or self._active_tab_id
            tab = self._tabs.get(tid)
            if tab and tab.history_idx > 0:
                tab.history_idx -= 1
                prev_url = tab.history[tab.history_idx]
                tab.url = prev_url
                tab.title = self._extract_title_hint(prev_url)
                tab.can_go_back = tab.history_idx > 0
                tab.can_go_forward = tab.history_idx < len(tab.history) - 1
            elif tab:
                tab.url = None
                tab.title = "New Tab"
                tab.history_idx = -1
                tab.can_go_back = False

        self._broadcast_state()
        if self._native_window and tab and tab.url:
            try:
                self._native_window.load_url(tab.url)
            except Exception:
                pass
        return self._tabs.get(tid, self.get_active_tab())

    def go_forward(self, tab_id: Optional[str] = None) -> BrowserTab:
        with self._lock:
            tid = tab_id or self._active_tab_id
            tab = self._tabs.get(tid)
            if tab and tab.history_idx < len(tab.history) - 1:
                tab.history_idx += 1
                next_url = tab.history[tab.history_idx]
                tab.url = next_url
                tab.title = self._extract_title_hint(next_url)
                tab.can_go_back = tab.history_idx > 0
                tab.can_go_forward = tab.history_idx < len(tab.history) - 1

        self._broadcast_state()
        if self._native_window and tab and tab.url:
            try:
                self._native_window.load_url(tab.url)
            except Exception:
                pass
        return self._tabs.get(tid, self.get_active_tab())

    def reload(self, tab_id: Optional[str] = None) -> BrowserTab:
        tab = self.get_active_tab()
        if tab and tab.url:
            if self._native_window:
                try:
                    self._native_window.load_url(tab.url)
                except Exception:
                    pass
        self._broadcast_state()
        return tab

    def create_tab(self, url: Optional[str] = None) -> BrowserTab:
        new_tab = BrowserTab()
        if url:
            new_tab.url = self._normalize_url(url)
            new_tab.title = self._extract_title_hint(new_tab.url)
            new_tab.history = [new_tab.url]
            new_tab.history_idx = 0

        with self._lock:
            self._tabs[new_tab.id] = new_tab
            self._active_tab_id = new_tab.id

        self._broadcast_state()
        if self._native_window and new_tab.url:
            try:
                self._native_window.load_url(new_tab.url)
            except Exception:
                pass
        return new_tab

    def close_tab(self, tab_id: str) -> BrowserState:
        with self._lock:
            if len(self._tabs) <= 1:
                # Reset single tab to home
                single = list(self._tabs.values())[0]
                single.url = None
                single.title = "New Tab"
                single.history = []
                single.history_idx = -1
                single.can_go_back = False
                single.can_go_forward = False
            else:
                self._tabs.pop(tab_id, None)
                if self._active_tab_id == tab_id:
                    self._active_tab_id = list(self._tabs.keys())[0]

        self._broadcast_state()
        return self.get_state()

    def switch_tab(self, tab_id: str) -> BrowserTab:
        with self._lock:
            if tab_id in self._tabs:
                self._active_tab_id = tab_id
            tab = self._tabs.get(self._active_tab_id)

        self._broadcast_state()
        if self._native_window and tab and tab.url:
            try:
                self._native_window.load_url(tab.url)
            except Exception:
                pass
        return tab or self.get_active_tab()

    def launch_native_view(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Launches a dedicated native Edge Chromium WebView2 instance with persistent profile."""
        target_url = self._normalize_url(url or (self.get_active_tab().url or "https://www.youtube.com/"))
        
        def _run_webview():
            try:
                import webview
                title = f"REZANE Browser — {self._extract_title_hint(target_url)}"
                
                # Configure webview settings for full web capability
                webview.settings['ALLOW_DOWNLOADS'] = True
                webview.settings['ALLOW_FILE_URLS'] = True
                webview.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False
                
                self._native_window = webview.create_window(
                    title=title,
                    url=target_url,
                    width=1180,
                    height=800,
                    resizable=True,
                    confirm_close=False,
                    background_color="#070709"
                )
                
                # Start webview with persistent storage path
                webview.start(
                    gui="edgechromium",
                    private_mode=False,
                    storage_path=str(BROWSER_PROFILE_DIR)
                )
            except Exception as e:
                logger.warning(f"Native WebView2 could not start directly, falling back to default browser: {e}")
                import webbrowser
                webbrowser.open(target_url)
            finally:
                self._native_window = None
                self._broadcast_state()

        if not self._native_thread or not self._native_thread.is_alive():
            self._native_thread = threading.Thread(target=_run_webview, daemon=True)
            self._native_thread.start()
            return {"status": "started", "url": target_url, "storage_path": str(BROWSER_PROFILE_DIR)}
        else:
            if self._native_window:
                try:
                    self._native_window.load_url(target_url)
                except Exception:
                    import webbrowser
                    webbrowser.open(target_url)
            else:
                import webbrowser
                webbrowser.open(target_url)
            return {"status": "navigated", "url": target_url}

    def _broadcast_state(self):
        state = self.get_state()
        event_bus.publish_nowait("browser_state", state.model_dump())


browser_manager = BrowserManager()
