import time
import requests
import socket
from datetime import datetime
from AppKit import NSWorkspace

# Mac Mini acts as the central Yuna server
YUNA_SERVER = "http://192.168.1.211:8000"  # Static IP for Mac Mini
DEVICE_NAME = "Mac Mini - Yuna Server"

def handle_memory_update():
    """Stores session memory locally on the Mac Mini."""
    session_memory = f"Session logged on {DEVICE_NAME} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    try:
        response = requests.post(f"{YUNA_SERVER}/update_yuna_memory", json={
            "new_memory": session_memory,
            "category": "server_logs"
        })
        print(f"📝 Server Memory Update: {response.json()}")
    except Exception as e:
        print(f"❌ Server Memory Update Failed: {e}")

def monitor_chatgpt():
    """Monitors ChatGPT usage on the Mac Mini."""
    print("🔍 Mac Mini monitoring ChatGPT...")
    while True:
        time.sleep(300)  # Runs every 5 minutes
        handle_memory_update()

if __name__ == "__main__":
    monitor_chatgpt()
