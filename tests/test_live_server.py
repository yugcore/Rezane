"""Integration test for live running server on localhost:8000."""
import asyncio
import json
import httpx
import websockets

async def test_live_server():
    print("Testing live REST API...")
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Health
        res = await client.get("/health")
        print("Health status:", res.status_code, res.json())
        assert res.status_code == 200

        # Status
        res = await client.get("/api/status")
        print("Assistant status:", res.json()["current_state"])

        # Windows
        res = await client.get("/api/windows")
        windows = res.json()["windows"]
        print(f"Discovered {len(windows)} active windows:")
        for w in windows[:3]:
            print(f"  - [{w['category']}] {w['title']} ({w['process_name']})")

        # Git
        res = await client.get("/api/git")
        git_data = res.json()
        print(f"Git repo: {git_data['repository']}, Branch: {git_data['branch']}, Modified: {len(git_data['modified'])}")

        # Chat
        res = await client.post("/api/chat", json={"text": "Check git"})
        print("Chat response:", res.status_code, res.json()["role"], res.json()["text"])

    print("\nTesting live WebSocket event stream...")
    async with websockets.connect("ws://127.0.0.1:8000/events") as ws:
        # Receive initial_sync
        msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
        event = json.loads(msg)
        print(f"Received WS event: '{event['event_type']}' with payload keys: {list(event.get('payload', {}).keys())}")
        assert event["event_type"] == "initial_sync"

        # Receive next telemetry event
        msg2 = await asyncio.wait_for(ws.recv(), timeout=6.0)
        event2 = json.loads(msg2)
        print(f"Received WS broadcast event: '{event2['event_type']}'")
        
    print("\n[OK] All live REST and WebSocket verification tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_live_server())
