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

# Structured document summarization
def structured_summarize_text(text):
    """Summarizes the document and extracts key points & action items."""
    try:
        prompt = "Summarize this document, extract key points, and suggest action items."
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

# Auto-categorize tasks
def categorize_task(task, due_date):
    """Categorizes tasks by urgency & type."""
    priority = "High" if "urgent" in task.lower() or "asap" in task.lower() else "Medium" if "soon" in task.lower() else "Low"
    category = "work" if "meeting" in task.lower() or "project" in task.lower() else "personal"
    collection.add(ids=[str(hash(task))], documents=[task], metadatas=[{"priority": priority, "category": category, "due_date": due_date}])
    return {"task": task, "category": category, "priority": priority, "due_date": due_date}

# Optimized memory recall
def fast_recall_memory(query):
    """Retrieves relevant memories with optimized search."""
    results = collection.query(query_texts=[query], n_results=5)
    return {"matching_memories": results.get("documents", [])}

# FastAPI Web App
app = FastAPI()

@app.get("/list_dropbox_files")
def get_dropbox_files():
    return list_dropbox_files()

@app.get("/structured_summarize_dropbox_doc")
def get_structured_summarized_doc(file: str):
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        _, response = dbx.files_download(f"{DROPBOX_FOLDER_PATH}{file}")
        text = response.content.decode("utf-8")
        return structured_summarize_text(text)
    except Exception as e:
        return {"error": str(e)}

@app.post("/add_task")
def add_task(task: str, due: str):
    return categorize_task(task, due)

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
