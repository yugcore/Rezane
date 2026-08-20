"""Configuration settings for Rezane AI Assistant Backend."""
from pathlib import Path
from pydantic import BaseModel

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = WORKSPACE_ROOT / "frontend"

class Settings(BaseModel):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    APP_NAME: str = "Rezane AI Assistant"
    VERSION: str = "0.1.0"
    
    # Security & CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "null",  # file:// origins
        "*"
    ]
    
    # Workspace paths
    WORKSPACE_PATH: Path = WORKSPACE_ROOT
    FRONTEND_PATH: Path = FRONTEND_DIR

settings = Settings()
