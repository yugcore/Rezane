"""Rezane AI Assistant — FastAPI Localhost Gateway & Event Server."""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response
from pydantic import BaseModel

from .config import settings
from .events.event_bus import event_bus
from .assistant.state_manager import state_manager, AssistantState
from .assistant.conversation import conversation_manager
from .host.windows_provider import windows_provider
from .host.git_provider import git_provider
from .tools.registry import tool_registry
from .tools.router import tool_router
from .browser import browser_manager
from .assistant.voice_engine import voice_engine
from fastapi import UploadFile, File

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("rezane.backend")

# Background telemetry broadcaster
async def telemetry_loop():
    logger.info("Starting background OS & Git telemetry loop...")
    while True:
        try:
            await asyncio.sleep(4.0)
            # Active Windows telemetry
            windows = windows_provider.list_active_windows()
            await event_bus.broadcast("windows_update", {
                "windows": [w.model_dump() for w in windows[:10]],
                "total_count": len(windows)
            })

            # Git telemetry
            git_data = git_provider.get_status()
            await event_bus.broadcast("git_update", git_data.model_dump())

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Telemetry loop iteration error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Rezane AI Assistant backend starting on {settings.HOST}:{settings.PORT} ...")
    task = asyncio.create_task(telemetry_loop())
    yield
    # Shutdown
    logger.info("Rezane AI Assistant backend shutting down...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Rezane AI Assistant Gateway",
    version=settings.VERSION,
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- REST Endpoints -----------------

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}

@app.get("/api/status")
async def get_assistant_status():
    return state_manager.status.model_dump()

class StateUpdateRequest(BaseModel):
    state: AssistantState
    status_text: Optional[str] = None

@app.post("/api/assistant/state")
async def set_assistant_state(req: StateUpdateRequest):
    state_manager.set_state(req.state, req.status_text)
    await event_bus.broadcast("state_change", state_manager.status.model_dump())
    return state_manager.status.model_dump()

@app.get("/api/windows")
async def get_active_windows():
    windows = windows_provider.list_active_windows()
    return {
        "windows": [w.model_dump() for w in windows],
        "total_count": len(windows)
    }

class FocusWindowRequest(BaseModel):
    hwnd: int

@app.post("/api/windows/focus")
async def focus_window(req: FocusWindowRequest):
    success = windows_provider.focus_window(req.hwnd)
    return {"status": "success" if success else "failed", "hwnd": req.hwnd}

@app.get("/api/git")
async def get_git_status():
    return git_provider.get_status().model_dump()

@app.get("/api/tools")
async def list_available_tools():
    return {"tools": tool_registry.list_tools()}

class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}
    user_confirmed: bool = False

@app.post("/api/tools/execute")
async def execute_tool_endpoint(req: ToolExecutionRequest):
    result = await tool_router.execute(
        tool_name=req.tool_name,
        parameters=req.parameters,
        user_confirmed=req.user_confirmed
    )
    return result.model_dump()

@app.get("/api/chat/history")
async def get_chat_history():
    messages = conversation_manager.get_history()
    return {"messages": [m.model_dump() for m in messages]}

class SendMessageRequest(BaseModel):
    text: str

@app.post("/api/chat")
async def send_chat_message(req: SendMessageRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")
    msg = await conversation_manager.handle_user_message(req.text)
    return msg.model_dump()

# ----------------- Voice & Speech-to-Text (STT) Endpoints -----------------

@app.get("/api/voice/status")
async def get_voice_status():
    return {
        "status": "ready" if voice_engine.is_ready else "initializing",
        "engine": "OpenAI Whisper",
        "model": voice_engine.model_name,
        "device": getattr(voice_engine, "_device", "auto"),
        "supports_continuous": True
    }

class VoiceCommandRequest(BaseModel):
    text: str

@app.post("/api/voice/command")
async def process_voice_command(req: VoiceCommandRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Command text cannot be empty")
    
    logger.info(f"Processing Voice Command: '{text}'")
    parsed = voice_engine.parse_voice_command(text)
    
    # Broadcast voice command event to frontend UI
    await event_bus.broadcast("voice_command", {
        "raw_text": text,
        "parsed": parsed,
        "timestamp": datetime.now().isoformat()
    })
    
    # If it is an action or conversational query, route through conversation manager
    if parsed.get("intent") in ["CHAT_QUERY", "ACTION"]:
        asyncio.create_task(conversation_manager.handle_user_message(text))
    elif parsed.get("intent") == "LAUNCH_APP":
        app_name = parsed.get("app")
        # Execute tool if mapped
        if app_name == "vscode":
            asyncio.create_task(tool_router.execute("launch_app", {"app_path": "code"}))
        elif app_name == "terminal":
            asyncio.create_task(tool_router.execute("launch_app", {"app_path": "wt"}))
        elif app_name == "explorer":
            asyncio.create_task(tool_router.execute("open_file_folder", {"path": "."}))

    return {"status": "ok", "parsed": parsed}

@app.post("/api/voice/transcribe")
async def transcribe_audio_endpoint(file: Optional[UploadFile] = File(None), audio_data: Optional[Dict[str, Any]] = Body(None)):
    import base64
    audio_bytes = b""
    filename = "audio.webm"
    
    if file:
        audio_bytes = await file.read()
        filename = file.filename or "audio.webm"
    elif audio_data and "base64" in audio_data:
        raw_b64 = audio_data["base64"]
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        audio_bytes = base64.b64decode(raw_b64)
        filename = audio_data.get("filename", "audio.webm")
    else:
        raise HTTPException(status_code=400, detail="No audio file or base64 data provided")
        
    result = await voice_engine.transcribe_audio_bytes(audio_bytes, filename=filename)
    
    # Auto-dispatch voice command if transcribed successfully
    transcribed_text = result.get("text", "").strip()
    if transcribed_text:
        parsed = voice_engine.parse_voice_command(transcribed_text)
        result["parsed"] = parsed
        await event_bus.broadcast("voice_command", {
            "raw_text": transcribed_text,
            "parsed": parsed,
            "timestamp": datetime.now().isoformat()
        })
        if parsed.get("intent") in ["CHAT_QUERY", "ACTION"]:
            asyncio.create_task(conversation_manager.handle_user_message(transcribed_text))
            
    return result

# ----------------- Embedded Browser Proxy -----------------

@app.get("/api/browser/proxy")
async def browser_proxy(url: str):
    import httpx
    import re
    from urllib.parse import urlparse

    target_url = url.strip()
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = f"https://{target_url}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Handle YouTube specific embeds
    if "youtube.com/watch" in target_url or "youtu.be/" in target_url:
        import urllib.parse
        video_id = ""
        if "youtu.be/" in target_url:
            video_id = target_url.split("youtu.be/")[1].split("?")[0].split("&")[0]
        elif "v=" in target_url:
            parsed = urllib.parse.urlparse(target_url)
            qs = urllib.parse.parse_qs(parsed.query)
            video_id = qs.get("v", [""])[0]
        
        if video_id:
            embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1&rel=0"
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <style>
                * {{ margin:0; padding:0; box-sizing:border-box; }}
                body {{ background:#080808; color:#f5f5f5; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; display:flex; flex-direction:column; height:100vh; overflow:hidden; }}
                .topbar {{ background:#0e0e0e; border-bottom:1px solid #222222; padding:8px 16px; display:flex; align-items:center; justify-content:space-between; height:42px; }}
                .badge {{ font-size:12px; color:#999999; display:flex; align-items:center; gap:6px; font-weight:600; }}
                .badge svg {{ width:14px; height:14px; fill:#ffffff; }}
                .btn-native {{ background:#ffffff; color:#000000; border:none; padding:5px 12px; border-radius:0px; font-size:11px; font-weight:700; cursor:pointer; text-decoration:none; display:flex; align-items:center; gap:5px; }}
                .btn-native:hover {{ background:#e0e0e0; }}
                .video-container {{ flex:1; position:relative; width:100%; height:calc(100vh - 42px); }}
                iframe {{ border:0; width:100%; height:100%; }}
              </style>
            </head>
            <body>
              <div class="topbar">
                <span class="badge">
                  <svg viewBox="0 0 24 24"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                  YouTube Embed Player
                </span>
                <button class="btn-native" onclick="fetch('/api/browser/native', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{url: '{target_url}'}})}})">
                  Open in Native Window
                </button>
              </div>
              <div class="video-container">
                <iframe src="{embed_url}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>
              </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html, status_code=200)

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, verify=False) as client:
            resp = await client.get(target_url, headers=headers)
            content_type = resp.headers.get("content-type", "text/html")

            if "text/html" in content_type:
                html = resp.text
                parsed = urlparse(str(resp.url))
                base_href = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if not base_href.endswith("/"):
                    base_href = base_href.rsplit("/", 1)[0] + "/"

                base_tag = f'<base href="{base_href}">'
                if "<head>" in html:
                    html = html.replace("<head>", f"<head>{base_tag}", 1)
                elif "<HEAD>" in html:
                    html = html.replace("<HEAD>", f"<HEAD>{base_tag}", 1)
                else:
                    html = f"{base_tag}{html}"

                return HTMLResponse(
                    content=html,
                    status_code=resp.status_code,
                    headers={
                        "X-Frame-Options": "ALLOWALL",
                        "Access-Control-Allow-Origin": "*"
                    }
                )
            else:
                return Response(
                    content=resp.content,
                    media_type=content_type,
                    status_code=resp.status_code
                )
    except Exception as e:
        error_html = f"""
        <html>
        <head>
          <style>
            body {{ background:#080808; color:#f5f5f5; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; display:flex; flex-direction:column; align-items:center; justify-content:center; height:80vh; text-align:center; padding:20px; }}
            .card {{ background:#0e0e0e; border:1px solid #222222; border-radius:0px; padding:24px; max-width:480px; box-shadow:0 8px 30px rgba(0,0,0,0.8); }}
            h3 {{ color:#ffffff; margin-bottom:8px; font-size:16px; }}
            p {{ color:#999999; font-size:13px; line-height:1.5; }}
            code {{ background:#1a1a1a; color:#e0e0e0; padding:2px 6px; border-radius:0px; font-family:monospace; }}
            .btn {{ display:inline-block; margin-top:14px; background:#ffffff; color:#000000; padding:6px 14px; border-radius:0px; text-decoration:none; font-size:12px; font-weight:700; }}
            .btn:hover {{ background:#e0e0e0; }}
          </style>
        </head>
        <body>
          <div class="card">
            <h3>Unable to load page in frame</h3>
            <p>Could not connect to: <code>{target_url}</code><br>Error: {str(e)}</p>
            <a class="btn" href="javascript:history.back()">Go Back</a>
          </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=502)

class NativeBrowserRequest(BaseModel):
    url: Optional[str] = None

@app.post("/api/browser/native")
async def launch_native_browser(req: Optional[NativeBrowserRequest] = None):
    target_url = req.url if (req and req.url) else None
    res = browser_manager.launch_native_view(target_url)
    return res

@app.get("/api/browser/state")
async def get_browser_state():
    return browser_manager.get_state().model_dump()

class QuickLaunchRequest(BaseModel):
    action: str

@app.post("/api/quicklaunch/action")
async def trigger_quicklaunch(req: QuickLaunchRequest):
    action = req.action.lower()
    if action in ("vscode", "vs code"):
        return (await tool_router.execute("open_application", {"name": "code"})).model_dump()
    elif action in ("terminal", "powershell"):
        return (await tool_router.execute("open_application", {"name": "powershell"})).model_dump()
    elif action in ("files", "explorer"):
        return (await tool_router.execute("open_folder", {"path": "."})).model_dump()
    elif action == "screenshot":
        return (await tool_router.execute("take_screenshot")).model_dump()
    else:
        return (await tool_router.execute("open_application", {"name": req.action})).model_dump()

# ----------------- WebSocket Events -----------------

@app.websocket("/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await event_bus.connect(websocket)
    try:
        await websocket.send_json({
            "event_type": "initial_sync",
            "payload": {
                "status": state_manager.status.model_dump(),
                "git": git_provider.get_status().model_dump(),
                "windows": [w.model_dump() for w in windows_provider.list_active_windows()[:10]],
                "history": [m.model_dump() for m in conversation_manager.get_history()]
            }
        })
        
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received WS message: {data}")
    except WebSocketDisconnect:
        await event_bus.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        await event_bus.disconnect(websocket)

# ----------------- Frontend Static Serving -----------------

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    async def serve_index():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Frontend not found, but backend is running."}
