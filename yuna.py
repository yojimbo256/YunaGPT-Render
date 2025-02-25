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

# Summarize text using OpenAI GPT-4
def summarize_text(text, detail_level="concise"):
    """Summarizes the given text using OpenAI GPT-4."""
    try:
        prompt = "Summarize the following document in a " + ("detailed" if detail_level == "detailed" else "concise") + " manner."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return f"Error in summarizing document: {str(e)}"

# Summarize selected Dropbox files
def summarize_selected_dropbox_docs(files, detail_level="concise"):
    summaries = {}
    for file_name in files:
        file_path = f"{DROPBOX_FOLDER_PATH}{file_name}"  # Ensure no extra '/'
        try:
            dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
            _, response = dbx.files_download(file_path)
            text = response.content.decode("utf-8")
            summary = summarize_text(text, detail_level)
            summaries[file_name] = summary
        except Exception as e:
            summaries[file_name] = f"Error: {e}"
    return summaries

# Task Reminders
def set_task_reminder(task, time):
    collection.add(ids=[str(hash(task))], documents=[task], metadatas=[{"reminder_time": time}])
    return {"message": "Task reminder set successfully."}

# Retrieve recent memories
def recall_recent_memories(days=7):
    cutoff_date = datetime.now() - timedelta(days=days)
    results = collection.query(query_texts=["*"], n_results=10)
    recent_memories = [mem for mem in results.get("documents", []) if "timestamp" in mem and datetime.strptime(mem["timestamp"], "%Y-%m-%d") >= cutoff_date]
    return {"recent_memories": recent_memories}

# Optimize memory queries manually
def optimize_memory_queries():
    """Performs manual cleanup of outdated memories in ChromaDB."""
    results = collection.query(query_texts=["*"], n_results=100)
    expired_memories = [mem["id"] for mem in results.get("metadatas", []) if "timestamp" in mem and datetime.strptime(mem["timestamp"], "%Y-%m-%d") < datetime.now() - timedelta(days=30)]
    
    if expired_memories:
        collection.delete(expired_memories)
    
    return {"message": f"Optimized memory. {len(expired_memories)} old records removed."}

# FastAPI Web App
app = FastAPI()

@app.get("/list_dropbox_files")
def get_dropbox_files():
    return list_dropbox_files()

@app.get("/summarize_selected_dropbox_docs")
def get_selected_summarized_docs(files: str, detail_level: str="concise"):
    file_list = files.split(",")
    return summarize_selected_dropbox_docs(file_list, detail_level)

@app.post("/set_task_reminder")
def create_task_reminder(task: str, time: str):
    return set_task_reminder(task, time)

@app.get("/recall_recent_memories")
def get_recent_memories(days: int=7):
    return recall_recent_memories(days)

@app.get("/optimize_memory_queries")
def optimize_memory():
    return optimize_memory_queries()

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 YunaGPT API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
