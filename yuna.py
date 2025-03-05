import os
import json
import asyncio
import sqlite3
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import subprocess

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rapidfuzz import fuzz

from memory import store_conversation, get_recent_conversations, delete_old_conversations

# === ✅ FastAPI App Initialization ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\U0001F680 Yuna API has started successfully!")
    yield

app = FastAPI(lifespan=lifespan)

# === ✅ CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yuna-web.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ✅ Environment Variables ===
PORT = int(os.getenv("PORT", "8000"))

# === ✅ Request Models ===
class ChatRequest(BaseModel):
    message: str

# === ✅ AI Response Generation ===
def generate_response(user_message: str) -> str:
    """Generate AI response locally or via Ollama."""
    try:
        response = subprocess.run(
            ["ollama", "run", "mistral"],
            input=user_message,
            text=True,
            capture_output=True
        )
        return response.stdout.strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"

# === ✅ Chat Endpoint (Saves to SQLite) ===
@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message
    ai_response = generate_response(user_message)

    # Store conversation in SQLite
    store_conversation(user_message, ai_response)

    return {"response": ai_response}

# === ✅ Fetch Chat History ===
@app.get("/history")
async def get_history(limit: int = 10):
    return {"conversations": get_recent_conversations(limit)}

# === ✅ Delete Old Conversations ===
@app.post("/delete_old_memories")
async def delete_memories(days: int = 30):
    delete_old_conversations(keep_latest=100)  # Keep the latest 100 messages
    return {"message": f"Deleted non-permanent conversations older than {days} days."}

# === ✅ Fuzzy Memory Search ===
@app.get("/search_memory")
async def search_memory(query: str):
    memories = get_recent_conversations(50)  # Search within the last 50 messages
    results = [mem for mem in memories if fuzz.partial_ratio(query, mem["user"]) > 70]
    return {"matches": results}

# === ✅ Start FastAPI Server ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
