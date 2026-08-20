"""Rezane AI Assistant — Advanced Voice-to-Text (STT) & Voice Command Engine."""
import asyncio
import io
import logging
import os
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("rezane.assistant.voice")

class VoiceEngine:
    """State-of-the-art Voice-to-Text Transcription Engine using OpenAI Whisper."""

    def __init__(self, model_name: str = "base.en"):
        self.model_name = model_name
        self._model = None
        self._lock = asyncio.Lock()
        self._device = "cuda"
        self.is_ready = False

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            import torch
            import whisper

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading Whisper STT model '{self.model_name}' on device: {self._device}...")
            self._model = whisper.load_model(self.model_name, device=self._device)
            self.is_ready = True
            logger.info("Whisper STT model loaded successfully.")
            return self._model
        except Exception as e:
            logger.warning(f"Whisper initialization note: {e}. Falling back to lightweight CPU mode.")
            try:
                import whisper
                self._device = "cpu"
                self._model = whisper.load_model("tiny.en", device="cpu")
                self.is_ready = True
                return self._model
            except Exception as e2:
                logger.error(f"Whisper load failed: {e2}")
                self.is_ready = False
                return None

    async def transcribe_audio_bytes(self, audio_bytes: bytes, filename: str = "audio.webm") -> Dict[str, Any]:
        """Transcribes incoming audio bytes to text using Whisper."""
        if not audio_bytes:
            return {"text": "", "error": "Empty audio payload", "confidence": 0.0}

        ext = os.path.splitext(filename)[1] or ".webm"
        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name

            # Run transcription in threadpool to avoid blocking event loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self._sync_transcribe, temp_path)
            return result
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            return {"text": "", "error": str(e), "confidence": 0.0}
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def _sync_transcribe(self, audio_path: str) -> Dict[str, Any]:
        model = self._load_model()
        if model is None:
            return {"text": "", "error": "Whisper STT model unavailable"}

        start_t = datetime.now()
        # FP16 is only for CUDA
        fp16 = (self._device == "cuda")
        result = model.transcribe(audio_path, fp16=fp16, language="en")
        duration = (datetime.now() - start_t).total_seconds()

        text = result.get("text", "").strip()
        logger.info(f"Transcribed audio in {duration:.2f}s: '{text}'")
        return {
            "text": text,
            "language": result.get("language", "en"),
            "duration": duration,
            "device": self._device,
            "engine": "openai-whisper"
        }

    def parse_voice_command(self, text: str) -> Dict[str, Any]:
        """Parses speech text for rapid UI popup/action intents."""
        t = text.lower().strip()
        if not t:
            return {"intent": "NONE", "raw": text}

        # 1. Hide / Close / Minimize back to pure Orb mode
        if any(w in t for w in ["close all", "hide all", "hide panel", "minimize", "go to sleep", "back to orb", "clean screen", "clear screen", "dismiss"]):
            return {"intent": "CLOSE_PANELS", "action": "close", "raw": text}

        # 2. Browser Popup Intents
        if any(w in t for w in ["open browser", "show browser", "browse youtube", "search google", "open web", "launch browser"]):
            # Extract search query if present
            query = ""
            if "search google for" in t:
                query = t.split("search google for", 1)[1].strip()
            elif "search youtube for" in t:
                query = t.split("search youtube for", 1)[1].strip()
            elif "google" in t:
                query = t.split("google", 1)[1].strip()
            elif "youtube" in t:
                query = t.split("youtube", 1)[1].strip()
            return {"intent": "OPEN_PANEL", "panel": "browser", "query": query, "raw": text}

        # 3. Quick Launch & Apps Popup
        if any(w in t for w in ["quick launch", "show apps", "launchpad", "app launcher", "show launch"]):
            return {"intent": "OPEN_PANEL", "panel": "quick_launch", "raw": text}

        # 4. Active Windows Popup
        if any(w in t for w in ["active windows", "show windows", "task manager", "open windows", "list windows"]):
            return {"intent": "OPEN_PANEL", "panel": "windows", "raw": text}

        # 5. Git Status Popup
        if any(w in t for w in ["git status", "show git", "check git", "open git", "git repository", "changes in git"]):
            return {"intent": "OPEN_PANEL", "panel": "git", "raw": text}

        # 6. AI Conversation / Chat Popup
        if any(w in t for w in ["show chat", "open chat", "ai output", "show conversation", "talk to rezane", "open assistant"]):
            return {"intent": "OPEN_PANEL", "panel": "chat", "raw": text}

        # 7. Full Dashboard HUD Expand
        if any(w in t for w in ["show dashboard", "open dashboard", "expand all", "show everything", "full dashboard"]):
            return {"intent": "OPEN_PANEL", "panel": "dashboard", "raw": text}

        # 8. Direct App Launchers
        if "launch vs code" in t or "open vs code" in t or "open code" in t:
            return {"intent": "LAUNCH_APP", "app": "vscode", "raw": text}
        if "open terminal" in t or "launch terminal" in t or "open powershell" in t:
            return {"intent": "LAUNCH_APP", "app": "terminal", "raw": text}
        if "open zegfx" in t or "launch zegfx" in t:
            return {"intent": "LAUNCH_APP", "app": "zegfx", "raw": text}
        if "open unreal" in t or "launch unreal" in t:
            return {"intent": "LAUNCH_APP", "app": "unreal", "raw": text}
        if "open godot" in t or "launch godot" in t:
            return {"intent": "LAUNCH_APP", "app": "godot", "raw": text}
        if "open explorer" in t or "open files" in t or "launch explorer" in t:
            return {"intent": "LAUNCH_APP", "app": "explorer", "raw": text}

        # 9. Screenshot / Build actions
        if "screenshot" in t or "capture screen" in t:
            return {"intent": "ACTION", "action": "take_screenshot", "raw": text}
        if "build zegfx" in t or "run benchmark" in t or "build renderer" in t:
            return {"intent": "ACTION", "action": "build_benchmark", "raw": text}

        # 10. General conversational query -> to Conversation Manager
        return {"intent": "CHAT_QUERY", "raw": text}

voice_engine = VoiceEngine()
