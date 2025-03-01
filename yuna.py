import os
import json
import asyncio
import sqlite3
from fastapi import FastAPI, Query, Request
import subprocess
from pydantic import BaseModel
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from rapidfuzz import fuzz

# Initialize FastAPI with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\U0001F680 Yuna API has started successfully with iCloud Drive storage!")
    yield

app = FastAPI()

# Load API Keys from Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN", "")
PORT = int(os.getenv("PORT", "8000"))

# Initialize ChromaDB for Vector Search
chroma_client = chromadb.PersistentClient(path="/home/yojimbo256/Yuna-AI/chroma_db")
collection = chroma_client.get_or_create_collection("yuna_knowledge")

# Define Storage Paths
LINUX_STORAGE_PATH = "/home/yojimbo256/Yuna-AI/data"
SHORT_TERM_MEMORY_PATH = f"{LINUX_STORAGE_PATH}/short_term_memory.json"
LONG_TERM_MEMORY_DB = f"{LINUX_STORAGE_PATH}/long_term_memory.db"

# Ensure JSON File Exists for Short-Term Memory
def ensure_json_file_exists(path, default_content):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default_content, f, indent=4)

ensure_json_file_exists(SHORT_TERM_MEMORY_PATH, {})
os.makedirs(LINUX_STORAGE_PATH, exist_ok=True)

# SQLite for Long-Term Memory
def init_long_term_memory():
    conn = sqlite3.connect(LONG_TERM_MEMORY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            content TEXT,
            category TEXT,
            summary TEXT,
            permanent INTEGER DEFAULT 0
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON memories(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
    conn.commit()
    conn.close()

init_long_term_memory()

# Request Models
class MemoryUpdateRequest(BaseModel):
    new_memory: str
    category: str
    permanent: bool = False

# Async File Handling
async def read_json(file_path):
    """Read JSON file asynchronously, handling errors."""
    try:
        if os.path.exists(file_path):
            return await asyncio.to_thread(lambda: json.load(open(file_path, "r")))
        return {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

async def write_json(file_path, data):
    await asyncio.to_thread(lambda: json.dump(data, open(file_path, "w"), indent=4))

# Generate Memory Summary
def generate_summary(memories):
    """Summarizes a list of memories before deletion."""
    return " ".join(mem["content"] for mem in memories[-5:]) if memories else ""

# Memory Management
@app.post("/update_yuna_memory")
async def save_memory_update(request: MemoryUpdateRequest):
    existing_memory = await read_json(SHORT_TERM_MEMORY_PATH)
    
    if request.category not in existing_memory:
        existing_memory[request.category] = []
    
    new_entry = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "content": request.new_memory
    }
    existing_memory[request.category].append(new_entry)
    await write_json(SHORT_TERM_MEMORY_PATH, existing_memory)
    
    # Save to Long-Term Memory if marked permanent
    if request.permanent:
        conn = sqlite3.connect(LONG_TERM_MEMORY_DB)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO memories (timestamp, content, category, permanent) VALUES (?, ?, ?, 1)",
                       (new_entry["timestamp"], request.new_memory, request.category))
        conn.commit()
        conn.close()
    
    return {"message": "Memory updated successfully."}

@app.get("/fetch_yuna_memory")
async def get_yuna_memory(category: str = Query(None)):
    short_term_memory = await read_json(SHORT_TERM_MEMORY_PATH)
    conn = sqlite3.connect(LONG_TERM_MEMORY_DB)
    cursor = conn.cursor()
    
    if category:
        cursor.execute("SELECT timestamp, content FROM memories WHERE category = ?", (category,))
        long_term_memory = cursor.fetchall()
        conn.close()
        return {"short_term": short_term_memory.get(category, []), "long_term": long_term_memory}
    
    cursor.execute("SELECT timestamp, content FROM memories")
    long_term_memory = cursor.fetchall()
    conn.close()
    return {"short_term": short_term_memory, "long_term": long_term_memory}

# Memory Cleanup
@app.post("/delete_old_memories")
async def delete_old_memories(days: int = 30):
    cutoff = datetime.now() - timedelta(days=days)
    conn = sqlite3.connect(LONG_TERM_MEMORY_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, category FROM memories WHERE timestamp < ? AND permanent = 0", (cutoff.strftime('%Y-%m-%d %H:%M:%S'),))
    old_memories = cursor.fetchall()
    
    if old_memories:
        summary = generate_summary([{"content": mem[1]} for mem in old_memories])
        cursor.execute("INSERT INTO memories (timestamp, content, category, permanent) VALUES (?, ?, ?, 1)",
                       (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), summary, "summary"))
    
    cursor.execute("DELETE FROM memories WHERE timestamp < ? AND permanent = 0", (cutoff.strftime('%Y-%m-%d %H:%M:%S'),))
    conn.commit()
    conn.close()
    return {"message": f"Deleted non-permanent memories older than {days} days."}

# Fuzzy Search
@app.get("/search_yuna_memory")
async def search_yuna_memory(query: str):
    conn = sqlite3.connect(LONG_TERM_MEMORY_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, content FROM memories")
    all_memories = cursor.fetchall()
    conn.close()
    
    results = [mem for mem in all_memories if fuzz.partial_ratio(query, mem[1]) > 70]
    return {"matches": results}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message")

    # Run local LLM using Ollama
    response = subprocess.run(
        ["ollama", "run", "mistral"],
        input=user_message,
        text=True,
        capture_output=True
    )

    return {"response": response.stdout}

# Start FastAPI Server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
