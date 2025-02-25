import os
import json
from fastapi import FastAPI
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

# Corrected Dropbox file path based on API response
DROPBOX_FOLDER_PATH = "/Apps/YunaGPT-Storage/yuna-docs/"

# Fetch list of files from Dropbox
def list_dropbox_files():
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        files = dbx.files_list_folder(DROPBOX_FOLDER_PATH).entries
        file_names = [file.name for file in files]
        return {"files": file_names}
    except Exception as e:
        print(f"Dropbox API Error: {e}")
        return {"error": "Could not retrieve file list."}

# Store text into memory
def remember_text(text):
    """Stores text into memory with a timestamp."""
    collection.add(
        ids=[str(hash(text))],  # Generate unique ID
        documents=[text],
        metadatas=[{"timestamp": datetime.now().strftime("%Y-%m-%d")}]
    )
    return {"message": "Memory stored successfully."}

# Retrieve stored memories
def fast_recall_memory(query):
    """Retrieves relevant memories with optimized search."""
    results = collection.query(query_texts=[query], n_results=5)
    return {"matching_memories": results.get("documents", [])}

# FastAPI Web App
app = FastAPI()

@app.get("/list_dropbox_files")
def get_dropbox_files():
    return list_dropbox_files()

@app.post("/remember")
def store_memory(text: str):
    return remember_text(text)

@app.get("/fast_recall_memory")
def get_fast_recall_memory(query: str):
    return fast_recall_memory(query)

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 YunaGPT API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
