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

# Fetch latest notes from Dropbox, summarize, tag, and auto-save them
def fetch_summarize_tag_and_save():
    """Fetches the latest text document from Dropbox, summarizes, tags it, and saves it back to Dropbox."""
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
        
        # Auto-save the summary to Dropbox
        write_to_dropbox(f"summary_{latest_file}", summary)
        
        return {"file": latest_file, "summary": summary, "tags": tags, "auto_saved": True}
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
    """Fetches, summarizes, tags, and auto-saves the latest Dropbox document."""
    return fetch_summarize_tag_and_save()

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
    print("\U0001F680 YunaGPT API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
