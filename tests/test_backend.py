"""Automated unit and integration tests for Rezane AI Backend."""
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings
from backend.events.event_bus import event_bus
from backend.assistant.state_manager import state_manager, AssistantState
from backend.permissions.engine import permission_engine, PermissionLevel
from backend.tools.registry import tool_registry
from backend.tools.router import tool_router
from backend.host.windows_provider import windows_provider
from backend.host.git_provider import git_provider
from backend.main import app

def test_settings():
    assert settings.PORT == 8000
    assert settings.HOST == "127.0.0.1"
    assert "http://localhost:8000" in settings.ALLOWED_ORIGINS

def test_permissions_engine():
    # Level 0 should auto-approve
    res0 = permission_engine.check_permission("read_clipboard", PermissionLevel.LEVEL_0_READ_ONLY, {})
    assert res0.allowed is True
    assert res0.requires_confirmation is False

    # Level 1 should approve with default auto-approve
    res1 = permission_engine.check_permission("open_application", PermissionLevel.LEVEL_1_LOW_RISK, {"name": "code"})
    assert res1.allowed is True

    # Level 2 should require confirmation if not user_confirmed
    res2 = permission_engine.check_permission("git_commit", PermissionLevel.LEVEL_2_DESTRUCTIVE, {"message": "test"}, user_confirmed=False)
    assert res2.allowed is False
    assert res2.requires_confirmation is True

    # Level 2 with user confirmation
    res2_ok = permission_engine.check_permission("git_commit", PermissionLevel.LEVEL_2_DESTRUCTIVE, {"message": "test"}, user_confirmed=True)
    assert res2_ok.allowed is True

def test_tool_registry():
    tools = tool_registry.list_tools()
    tool_names = [t.name for t in tools]
    assert "open_application" in tool_names
    assert "git_status" in tool_names
    assert "take_screenshot" in tool_names
    assert "read_clipboard" in tool_names

async def test_state_manager_transitions():
    await state_manager.set_state(AssistantState.LISTENING, "Listening for input")
    assert state_manager.status.current_state == AssistantState.LISTENING

    await state_manager.set_state(AssistantState.THINKING, "Thinking")
    assert state_manager.status.current_state == AssistantState.THINKING
    assert state_manager.status.previous_state == AssistantState.LISTENING

    task = await state_manager.start_task("t1", "Build Project", ["Configure", "Compile"])
    assert task.progress == 0
    assert state_manager.status.current_state == AssistantState.EXECUTING

    await state_manager.update_task_step(0, "done", progress=50)
    assert state_manager.status.active_task.progress == 50

    await state_manager.complete_task("Done")
    assert state_manager.status.current_state == AssistantState.IDLE

async def test_tool_router_execution():
    # Test read_clipboard or git_status tool
    res = await tool_router.execute("git_status", {})
    assert res.tool_name == "git_status"
    assert res.execution_time_ms >= 0

def test_windows_provider():
    windows = windows_provider.list_active_windows()
    assert isinstance(windows, list)
    # Check ActiveWindow structure
    if windows:
        w = windows[0]
        assert hasattr(w, 'hwnd')
        assert hasattr(w, 'title')
        assert hasattr(w, 'process_name')
        assert hasattr(w, 'category')

def test_git_provider():
    git = git_provider.get_status()
    assert hasattr(git, 'is_git')
    assert hasattr(git, 'branch')
    assert hasattr(git, 'modified')

def test_api_endpoints():
    from starlette.testclient import TestClient
    client = TestClient(app)
    
    # /health
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "ok"

    # /api/status
    r_status = client.get("/api/status")
    assert r_status.status_code == 200
    assert "current_state" in r_status.json()

    # /api/windows
    r_win = client.get("/api/windows")
    assert r_win.status_code == 200
    assert "windows" in r_win.json()

    # /api/git
    r_git = client.get("/api/git")
    assert r_git.status_code == 200
    assert "branch" in r_git.json()

    # /api/tools
    r_tools = client.get("/api/tools")
    assert r_tools.status_code == 200
    assert len(r_tools.json()["tools"]) > 0

    # /api/voice/status
    r_voice = client.get("/api/voice/status")
    assert r_voice.status_code == 200
    assert "engine" in r_voice.json()

    # /api/voice/command
    r_cmd = client.post("/api/voice/command", json={"text": "open browser"})
    assert r_cmd.status_code == 200
    assert r_cmd.json()["parsed"]["intent"] == "OPEN_PANEL"
    assert r_cmd.json()["parsed"]["panel"] == "browser"

def test_voice_parser():
    from backend.assistant.voice_engine import voice_engine
    p1 = voice_engine.parse_voice_command("open browser and search youtube")
    assert p1["intent"] == "OPEN_PANEL"
    assert p1["panel"] == "browser"

    p2 = voice_engine.parse_voice_command("show active windows")
    assert p2["intent"] == "OPEN_PANEL"
    assert p2["panel"] == "windows"

    p3 = voice_engine.parse_voice_command("close all")
    assert p3["intent"] == "CLOSE_PANELS"

if __name__ == "__main__":
    test_settings()
    test_permissions_engine()
    test_tool_registry()
    test_windows_provider()
    test_git_provider()
    test_voice_parser()
    test_api_endpoints()
    asyncio.run(test_state_manager_transitions())
    asyncio.run(test_tool_router_execution())
    print("All unit, API, and voice integration tests passed successfully!")

