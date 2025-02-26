import os
import json
from fastapi import FastAPI, Query
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
    category: str  # Allow categorization of memory

class DeleteMemoryRequest(BaseModel):
    days: int  # Number of days to keep, delete older

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
def update_yuna_memory(new_memory, category):
    """Updates Yuna's persistent memory in Dropbox, sorted by category."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        file_path = f"{DROPBOX_FOLDER_PATH}yuna_memory.json"
        
        try:
            _, response = dbx.files_download(file_path)
            existing_memory = json.loads(response.content.decode("utf-8"))
        except dropbox.exceptions.ApiError:
            existing_memory = {"tasks": [], "summaries": [], "general": []}

        if category not in existing_memory:
            existing_memory[category] = []

        existing_memory[category].append({
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "content": new_memory
        })

        dbx.files_upload(json.dumps(existing_memory, indent=4).encode("utf-8"), file_path, mode=dropbox.files.WriteMode("overwrite"))
        return {"message": "Memory updated successfully in Dropbox."}
    except Exception as e:
        print(f"Memory Update Error: {e}")
        return {"error": str(e)}

# Keyword-Based Memory Search
def search_yuna_memory(query: str):
    """Searches Yuna's stored memory for specific keywords."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        file_path = f"{DROPBOX_FOLDER_PATH}yuna_memory.json"
        _, response = dbx.files_download(file_path)
        memory_data = json.loads(response.content.decode("utf-8"))
        results = []

        for category in memory_data:
            results.extend([entry for entry in memory_data[category] if query.lower() in entry["content"].lower()])

        return {"results": results}
    except dropbox.exceptions.ApiError:
        return {"error": "Memory file not found."}
    except Exception as e:
        print(f"Memory Search Error: {e}")
        return {"error": str(e)}

# Summarize Stored Memory
def summarize_yuna_memory():
    """Generates a summary of stored memories."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        file_path = f"{DROPBOX_FOLDER_PATH}yuna_memory.json"
        _, response = dbx.files_download(file_path)
        memory_data = json.loads(response.content.decode("utf-8"))
        all_text = "\n".join([entry["content"] for category in memory_data for entry in memory_data[category]])

        summary = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize the following memory data."},
                {"role": "user", "content": all_text}
            ]
        )
        return {"summary": summary["choices"][0]["message"]["content"]}
    except Exception as e:
        print(f"Memory Summarization Error: {e}")
        return {"error": str(e)}

@app.get("/search_memory")
def search_memory(query: str = Query(...)):
    return search_yuna_memory(query)

@app.get("/summarize_yuna_memory")
def get_memory_summary():
    return summarize_yuna_memory()

@app.post("/delete_old_memories")
def delete_old_entries(request: DeleteMemoryRequest):
    """Deletes memories older than a given number of days."""
    return delete_old_memories(request.days)

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 Yuna API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
