import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
import openai
import chromadb
from chromadb.utils import embedding_functions
from github import Github
import requests
import dropbox
from datetime import datetime, timedelta

# Load API Keys from Render Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
PORT = int(os.getenv("PORT", 8000))  # Default to 8000 if not set

# Initialize OpenAI Client
openai.api_key = OPENAI_API_KEY 

# Initialize ChromaDB for Persistent Memory
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("yuna_knowledge")

# Corrected Dropbox file path
DROPBOX_FOLDER_PATH = "/Apps/YunaGPT-Storage/yuna-docs/"

# Define Pydantic models for JSON requests
class DropboxRequest(BaseModel):
    file_name: str
    content: str

class UpdateDropboxRequest(BaseModel):
    file_name: str
    update_content: str

class MemoryUpdateRequest(BaseModel):
    new_memory: str

# Define write_to_dropbox to ensure it's available
def write_to_dropbox(file_name: str, content: str):
    """Writes or updates a file in Dropbox."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        file_path = f"{DROPBOX_FOLDER_PATH}{file_name}"
        dbx.files_upload(content.encode("utf-8"), file_path, mode=dropbox.files.WriteMode("overwrite"))
        return {"message": f"Successfully written to {file_name} in Dropbox."}
    except Exception as e:
        print(f"Dropbox Write Error: {e}")
        return {"error": str(e)}

# Update Yuna's persistent memory
def update_yuna_memory(new_memory):
    """Updates Yuna's persistent memory in Dropbox."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        file_path = f"{DROPBOX_FOLDER_PATH}yuna_memory.json"
        
        try:
            _, response = dbx.files_download(file_path)
            existing_memory = json.loads(response.content.decode("utf-8"))
        except dropbox.exceptions.ApiError:
            existing_memory = {"memories": []}

        existing_memory["memories"].append({
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "content": new_memory
        })

        dbx.files_upload(json.dumps(existing_memory, indent=4).encode("utf-8"), file_path, mode=dropbox.files.WriteMode("overwrite"))
        return {"message": "Memory updated successfully in Dropbox."}
    except Exception as e:
        print(f"Memory Update Error: {e}")
        return {"error": str(e)}

# Fetch Yuna's memory from Dropbox
def fetch_yuna_memory():
    """Fetches stored memory from Dropbox."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        file_path = f"{DROPBOX_FOLDER_PATH}yuna_memory.json"
        _, response = dbx.files_download(file_path)
        return json.loads(response.content.decode("utf-8"))
    except dropbox.exceptions.ApiError:
        return {"error": "Memory file not found."}
    except Exception as e:
        print(f"Memory Fetch Error: {e}")
        return {"error": str(e)}

# FastAPI Web App
app = FastAPI()

@app.post("/update_yuna_memory")
def save_memory_update(request: MemoryUpdateRequest):
    """Saves session updates into Yuna's memory."""
    return update_yuna_memory(request.new_memory)

@app.get("/fetch_yuna_memory")
def get_yuna_memory():
    """Retrieves stored memories from Dropbox."""
    return fetch_yuna_memory()

@app.get("/fetch_latest_notes_with_summary_and_tags")
def get_latest_notes_with_summary_and_tags():
    """Fetches, prioritizes projects.md, and retrieves Dropbox document."""
    return fetch_latest_notes_with_summary_and_tags()

@app.post("/write_to_dropbox")
def save_to_dropbox(request: DropboxRequest):
    """Writes or updates a file in Dropbox."""
    return write_to_dropbox(request.file_name, request.content)

@app.post("/update_dropbox_file")
def append_to_dropbox(request: UpdateDropboxRequest):
    """Appends updates to an existing Dropbox file."""
    return update_dropbox_file(request.file_name, request.update_content)

@app.post("/generate_scheduled_summary")
def run_scheduled_summary():
    """Runs the scheduled summary and task reminder process."""
    return generate_scheduled_summary()

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 Yuna API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
