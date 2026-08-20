"""Main executable launcher for Rezane AI Assistant."""
import sys
import socket
import webbrowser
import uvicorn
from backend.config import settings

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.8)
        return s.connect_ex((host, port)) == 0

def main():
    print("=" * 60)
    print(f"Rezane AI Assistant v{settings.VERSION}")
    print(f"Backend Gateway: http://{settings.HOST}:{settings.PORT}")
    print(f"WebSocket Stream: ws://{settings.HOST}:{settings.PORT}/events")
    print(f"Assistant Dashboard: http://{settings.HOST}:{settings.PORT}/")
    print("=" * 60)

    url = f"http://{settings.HOST}:{settings.PORT}/"

    if is_port_in_use(settings.PORT, settings.HOST):
        print(f"\n[INFO] Assistant backend is already running on port {settings.PORT}.")
        print(f"Opening dashboard at {url} ...\n")
        if "--no-browser" not in sys.argv:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        return

    # Automatically open the dashboard in browser if requested
    if "--no-browser" not in sys.argv:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
