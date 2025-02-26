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

# Define Pydantic model for JSON requests
class DropboxRequest(BaseModel):
    file_name: str
    content: str

class UpdateDropboxRequest(BaseModel):
    file_name: str
    update_content: str

# Fetch latest notes from Dropbox, prioritize projects.md
def fetch_latest_notes_with_summary_and_tags():
    """Fetches `projects.md` from Dropbox if it exists, otherwise fetches the most recent text file."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        files = dbx.files_list_folder(DROPBOX_FOLDER_PATH).entries
        text_files = [file.name for file in files if file.name.endswith(".md") or file.name.endswith(".txt")]
        
        if "projects.md" in text_files:
            latest_file = "projects.md"
        elif text_files:
            latest_file = sorted(text_files, reverse=True)[0]
        else:
            return {"error": "No text files found in Dropbox."}
        
        _, response = dbx.files_download(f"{DROPBOX_FOLDER_PATH}{latest_file}")
        content = response.content.decode("utf-8")
        
        return {"file": latest_file, "content": content}
    except Exception as e:
        print(f"Dropbox API Error: {e}")
        return {"error": str(e)}

# Write content to Dropbox
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

# Append updates to an existing Dropbox file
def update_dropbox_file(file_name: str, update_content: str):
    """Appends new content to an existing Dropbox file, or creates it if it doesn’t exist."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        file_path = f"{DROPBOX_FOLDER_PATH}{file_name}"
        try:
            _, response = dbx.files_download(file_path)
            existing_content = response.content.decode("utf-8")
            updated_content = existing_content + "\n" + update_content
        except dropbox.exceptions.ApiError:
            print(f"File {file_name} does not exist. Creating a new one.")
            updated_content = update_content
        
        dbx.files_upload(updated_content.encode("utf-8"), file_path, mode=dropbox.files.WriteMode("overwrite"))
        return {"message": f"Updated {file_name} in Dropbox."}
    except Exception as e:
        print(f"Dropbox Update Error: {e}")
        return {"error": str(e)}

# FastAPI Web App
app = FastAPI()

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

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 Yuna API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
