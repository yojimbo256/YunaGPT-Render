import os
import json
import asyncio
from fastapi import FastAPI, Query
from pydantic import BaseModel
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime
from contextlib import asynccontextmanager

# Initialize FastAPI with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\U0001F680 Yuna API has started successfully on Mac Mini!")
    yield  # Keeps the app running

app = FastAPI(lifespan=lifespan)

# Load API Keys from Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN", "")
try:
    PORT = int(os.getenv("PORT", "8000"))  # Default to 8000 if not set
except ValueError:
    PORT = 8000  # Fallback to default

# Initialize ChromaDB for Persistent Memory
chroma_client = chromadb.PersistentClient(path="/usr/local/yuna/chroma_db")  # Persistent storage
collection = chroma_client.get_or_create_collection("yuna_knowledge")

# Define Local Storage Paths
LOCAL_MEMORY_PATH = "/usr/local/yuna/yuna_memory.json"
LOCAL_TASKS_PATH = "/usr/local/yuna/yuna_tasks.json"
LOCAL_LOG_PATH = "/usr/local/yuna/yuna_log.txt"

# Ensure Files Exist
def ensure_file_exists(path, default_content):
    """Ensure that required files exist with default content if missing."""
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default_content, f, indent=4) if isinstance(default_content, (dict, list)) else f.write(default_content)

ensure_file_exists(LOCAL_MEMORY_PATH, {})
ensure_file_exists(LOCAL_TASKS_PATH, [])
ensure_file_exists(LOCAL_LOG_PATH, "")

# Define Request Models
class MemoryUpdateRequest(BaseModel):
    new_memory: str
    category: str  # Allow categorization of memory

class TaskRequest(BaseModel):
    task: str
    priority: str = "normal"  # low, normal, high
    due_date: str = None  # Optional deadline
    status: str = "pending"  # pending, completed

# Async File Handling
async def read_json_file(file_path, default):
    """Read JSON file asynchronously, handling errors."""
    try:
        if os.path.exists(file_path):
            async with asyncio.to_thread(open, file_path, "r") as f:
                return json.load(f)
        return default
    except (json.JSONDecodeError, FileNotFoundError):
        return default

async def write_json_file(file_path, data):
    """Write JSON file asynchronously."""
    async with asyncio.to_thread(open, file_path, "w") as f:
        json.dump(data, f, indent=4)

# Memory Management
@app.post("/update_yuna_memory")
async def save_memory_update(request: MemoryUpdateRequest):
    existing_memory = await read_json_file(LOCAL_MEMORY_PATH, {})
    
    if request.category not in existing_memory:
        existing_memory[request.category] = []
    
    existing_memory[request.category].append({
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "content": request.new_memory
    })
    
    await write_json_file(LOCAL_MEMORY_PATH, existing_memory)
    return {"message": "Memory updated successfully."}

@app.get("/fetch_yuna_memory")
async def get_yuna_memory(category: str = Query(None)):
    memory_data = await read_json_file(LOCAL_MEMORY_PATH, {})
    return memory_data if not category else {category: memory_data.get(category, [])}

# Task Management
@app.get("/fetch_tasks")
async def get_tasks():
    tasks = await read_json_file(LOCAL_TASKS_PATH, [])
    return tasks if tasks else {"message": "No tasks found."}

@app.post("/add_task")
async def add_task(request: TaskRequest):
    tasks = await read_json_file(LOCAL_TASKS_PATH, [])
    task_entry = {
        "task": request.task,
        "priority": request.priority,
        "due_date": request.due_date,
        "status": request.status,
        "added": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    tasks.append(task_entry)
    await write_json_file(LOCAL_TASKS_PATH, tasks)
    return {"message": "Task added successfully."}

@app.post("/update_task_status")
async def update_task_status(index: int, new_status: str):
    tasks = await read_json_file(LOCAL_TASKS_PATH, [])
    if 0 <= index < len(tasks):
        tasks[index]["status"] = new_status
        await write_json_file(LOCAL_TASKS_PATH, tasks)
        return {"message": f"Task {index} updated to {new_status}."}
    return {"error": "Invalid task index."}

# Log Management
@app.get("/logs")
async def fetch_logs():
    try:
        async with asyncio.to_thread(open, LOCAL_LOG_PATH, "r") as f:
            logs = f.readlines()
        return {"logs": logs if logs else ["No logs available."]}
    except FileNotFoundError:
        return {"logs": ["No logs available."]}

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
