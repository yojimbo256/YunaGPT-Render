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

# Auto-delete outdated tasks & projects
def auto_delete_old_entries():
    """Deletes tasks and projects older than 30 days."""
    try:
        results = collection.query(query_texts=["*"], n_results=100)
        expired_entries = []
        cutoff_date = datetime.now() - timedelta(days=30)

        for entry in results.get("metadatas", []):
            if "timestamp" in entry and isinstance(entry["timestamp"], str):
                try:
                    entry_date = datetime.strptime(entry["timestamp"], "%Y-%m-%d")
                    if entry_date < cutoff_date:
                        expired_entries.append(entry["id"])
                except ValueError:
                    continue  # Skip entries with invalid timestamps

        if expired_entries:
            collection.delete(expired_entries)
        return {"message": f"Deleted {len(expired_entries)} outdated entries."}
    except Exception as e:
        print(f"Deletion Error: {e}")
        return {"error": str(e)}

# Scheduled summaries & task reminders
def generate_scheduled_summary():
    """Generates a daily report of Dropbox updates and upcoming tasks."""
    try:
        from yuna import fetch_latest_notes_with_summary_and_tags  # Ensure proper reference
        notes_response = fetch_latest_notes_with_summary_and_tags()
        tasks_response = check_upcoming_tasks()
        
        summary_content = f"### Daily Report ({datetime.now().strftime('%Y-%m-%d')})\n\n"
        summary_content += "#### Dropbox Updates\n" + json.dumps(notes_response, indent=4) + "\n\n"
        summary_content += "#### Upcoming Tasks\n" + json.dumps(tasks_response, indent=4) + "\n"
        
        write_to_dropbox("daily_report.md", summary_content)
        return {"message": "Daily report generated and saved to Dropbox."}
    except Exception as e:
        print(f"Scheduled Summary Error: {e}")
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

@app.post("/auto_delete_old_entries")
def cleanup_old_entries():
    """Deletes outdated tasks and projects."""
    return auto_delete_old_entries()

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
