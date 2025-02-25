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

# Fetch latest notes from Dropbox, summarize, and tag them
def fetch_summarize_tag_dropbox_notes():
    """Fetches the latest text document from Dropbox, summarizes, and tags it."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        files = dbx.files_list_folder(DROPBOX_FOLDER_PATH).entries
        text_files = [file.name for file in files if file.name.endswith(".txt")]
        if not text_files:
            return {"error": "No text files found in Dropbox."}
        
        latest_file = sorted(text_files, reverse=True)[0]
        _, response = dbx.files_download(f"{DROPBOX_FOLDER_PATH}{latest_file}")
        content = response.content.decode("utf-8")
        
        # Summarize document
        summary = summarize_text(content)
        
        # Tag document based on content
        tags = generate_tags(summary)
        
        # Store summary and tags in memory
        store_summary(latest_file, summary, tags)
        
        return {"file": latest_file, "summary": summary, "tags": tags}
    except Exception as e:
        print(f"Dropbox API Error: {e}")
        return {"error": str(e)}

# Summarization function
def summarize_text(text):
    """Summarizes the given text using OpenAI GPT-4."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize the following document concisely."},
                {"role": "user", "content": text}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return f"Error in summarizing document: {str(e)}"

# Generate tags for document
def generate_tags(text):
    """Generates topic tags for a given text."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract topic tags from the following text."},
                {"role": "user", "content": text}
            ]
        )
        return ", ".join(response["choices"][0]["message"]["content"].split(", "))
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return "error"

# Store summary and tags in memory
def store_summary(file_name, summary, tags):
    """Stores the summarized document in memory along with topic tags."""
    collection.add(
        ids=[str(hash(file_name))],
        documents=[summary],
        metadatas=[{"file_name": file_name, "tags": tags, "timestamp": datetime.now().strftime("%Y-%m-%d")}]
    )
    print(f"Stored summary for {file_name} in memory with tags {tags}.")

# Write content to Dropbox via JSON request
def write_to_dropbox(file_name: str, content: str):
    """Writes a new file or updates an existing file in Dropbox."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        file_path = f"{DROPBOX_FOLDER_PATH}{file_name}"
        dbx.files_upload(content.encode("utf-8"), file_path, mode=dropbox.files.WriteMode("overwrite"))
        return {"message": f"Successfully written to {file_name} in Dropbox."}
    except Exception as e:
        print(f"Dropbox Write Error: {e}")
        return {"error": str(e)}

# FastAPI Web App
app = FastAPI()

@app.get("/fetch_latest_notes_with_summary_and_tags")
def get_latest_notes_with_summary_and_tags():
    """Fetches, summarizes, and tags the latest Dropbox document."""
    return fetch_summarize_tag_dropbox_notes()

@app.post("/write_to_dropbox")
def save_to_dropbox(request: DropboxRequest):
    """Writes or updates a file in Dropbox."""
    return write_to_dropbox(request.file_name, request.content)

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 YunaGPT API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
