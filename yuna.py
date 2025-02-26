import os
import json
from fastapi import FastAPI, Query
from pydantic import BaseModel
import requests
import chromadb
from chromadb.utils import embedding_functions
from github import Github
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Initialize FastAPI with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\U0001F680 Yuna API has started successfully on Mac Mini!")
    yield  # Keeps the app running

app = FastAPI(lifespan=lifespan)

# Load API Keys from Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
PORT = int(os.getenv("PORT", 8000))  # Default to 8000 if not set

# Initialize ChromaDB for Persistent Memory
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("yuna_knowledge")

# Define Local Storage Paths
LOCAL_MEMORY_PATH = "/usr/local/yuna/yuna_memory.json"
LOCAL_TASKS_PATH = "/usr/local/yuna/yuna_tasks.json"
LOCAL_LOG_PATH = "/usr/local/yuna/yuna_log.txt"

# Ensure Files Exist
for path, default_content in [(LOCAL_MEMORY_PATH, {}), (LOCAL_TASKS_PATH, []), (LOCAL_LOG_PATH, "")]:
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default_content, f) if isinstance(default_content, dict) or isinstance(default_content, list) else f.write(default_content)

# Define Request Models
class MemoryUpdateRequest(BaseModel):
    new_memory: str
    category: str  # Allow categorization of memory

class TaskRequest(BaseModel):
    task: str

# Memory Management Functions
def update_yuna_memory(new_memory, category):
    try:
        with open(LOCAL_MEMORY_PATH, "r") as f:
            existing_memory = json.load(f)
        if category not in existing_memory:
            existing_memory[category] = []
        existing_memory[category].append({
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "content": new_memory
        })
        with open(LOCAL_MEMORY_PATH, "w") as f:
            json.dump(existing_memory, f, indent=4)
        return {"message": "Memory updated successfully."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/update_yuna_memory")
def save_memory_update(request: MemoryUpdateRequest):
    return update_yuna_memory(request.new_memory, request.category)

@app.get("/fetch_yuna_memory")
def get_yuna_memory(category: str = Query(None)):
    try:
        with open(LOCAL_MEMORY_PATH, "r") as f:
            memory_data = json.load(f)
        return memory_data if not category else {category: memory_data.get(category, [])}
    except Exception as e:
        return {"error": str(e)}

@app.get("/fetch_tasks")
def get_tasks():
    try:
        with open(LOCAL_TASKS_PATH, "r") as f:
            tasks = json.load(f)
        return tasks if tasks else {"message": "No tasks found."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/logs")
def fetch_logs():
    try:
        with open(LOCAL_LOG_PATH, "r") as f:
            logs = f.readlines()
        return {"logs": logs if logs else ["No logs available."]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/add_task")
def add_task(request: TaskRequest):
    try:
        with open(LOCAL_TASKS_PATH, "r") as f:
            tasks = json.load(f)
        tasks.append({"task": request.task, "added": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        with open(LOCAL_TASKS_PATH, "w") as f:
            json.dump(tasks, f, indent=4)
        return {"message": "Task added successfully."}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
