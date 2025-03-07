import os
import json
import asyncio
import sqlite3
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rapidfuzz import fuzz

# === ✅ FastAPI App Initialization ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\U0001F680 Yuna API has started successfully with HTTPS!")
    yield

app = FastAPI(lifespan=lifespan)

# === ✅ Updated CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yuna-web.vercel.app"],  # Restrict to trusted frontend
    allow_credentials=True,
    allow_methods=["OPTIONS", "GET", "POST"],
    allow_headers=["*"]
)

# === ✅ Environment Variables ===
PORT = int(os.getenv("PORT", "8000"))
DB_PATH = "yuna_memory.db"

# === ✅ Database Helper Functions ===
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            yuna TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()

init_db()

def store_conversation(user_message: str, yuna_response: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (user, yuna) VALUES (?, ?)", (user_message, yuna_response)
    )
    conn.commit()
    conn.close()

def get_recent_conversations(limit: int = 5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user, yuna FROM conversations ORDER BY timestamp DESC LIMIT ?", (limit,)
    )
    memory = [{"user": row[0], "yuna": row[1]} for row in cursor.fetchall()]
    conn.close()
    return memory

# === ✅ Request Models ===
class ChatRequest(BaseModel):
    message: str

# === ✅ AI Response Generation ===
def generate_response(user_message: str) -> str:
    """Generate AI response while limiting redundant memory recall."""
    personality = "I am Yuna, your AI assistant. I assist with insights, memory recall, and intelligent discussions."

    # Fetch last 5 interactions, ensuring uniqueness
    memory = get_recent_conversations(limit=5)
    seen_messages = set()
    filtered_memory = []

    for entry in memory:
        if entry["user"] not in seen_messages:
            filtered_memory.append(entry)
            seen_messages.add(entry["user"])

    # Keep only last 3 unique interactions
    context_summary = "\n".join([f"{m['user']}: {m['yuna']}" for m in filtered_memory[-3:]])
    response = f"{personality}\n\nRecent relevant context:\n{context_summary}\n\nUser: {user_message}\nYuna:"
    return response

# === ✅ Chat Endpoint ===
@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message
    ai_response = generate_response(user_message)
    store_conversation(user_message, ai_response)
    return {"response": ai_response}

# === ✅ Fetch Chat History ===
@app.get("/history")
async def get_history(limit: int = 10):
    """Fetch conversation history with better filtering and summarization."""
    memory = get_recent_conversations(limit)
    seen_users = set()
    unique_conversations = []

    for entry in memory:
        if entry["user"] not in seen_users:
            unique_conversations.append(entry)
            seen_users.add(entry["user"])

    return {"conversations": unique_conversations}

# === ✅ Start FastAPI Server with HTTPS ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, ssl_keyfile="/home/yojimbo256/server.key", ssl_certfile="/home/yojimbo256/server.crt")
