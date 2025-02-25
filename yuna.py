import os
import json
from fastapi import FastAPI
import openai
import chromadb
from chromadb.utils import embedding_functions
from github import Github
import requests
import dropbox
from datetime import datetime

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

# Multi-file summarization
def multi_summarize_dropbox_docs():
    files = list_dropbox_files()
    summaries = {}
    for file_name in files.get("files", []):
        file_path = f"{DROPBOX_FOLDER_PATH}{file_name}"  # Ensure no extra '/'
        try:
            dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
            _, response = dbx.files_download(file_path)
            text = response.content.decode("utf-8")
            summary = summarize_text(text)
            summaries[file_name] = summary
        except Exception as e:
            summaries[file_name] = f"Error: {e}"
    return summaries

# Extract key points from a document
def extract_key_points(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract key points from the following document."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return "Error extracting key points."

# Task Management in ChromaDB
def add_task(task, due_date, priority="medium"):
    collection.add(ids=[str(hash(task))], documents=[task], metadatas=[{"due_date": due_date, "priority": priority}])
    return {"message": "Task added successfully."}

def list_tasks():
    results = collection.query(n_results=10)
    if results and "documents" in results:
        return {"tasks": results["documents"]}
    else:
        return {"error": "No tasks found."}

def list_high_priority_tasks():
    results = collection.query(n_results=10)
    high_priority_tasks = [task for task in results.get("documents", []) if task.get("priority") == "high"]
    return {"high_priority_tasks": high_priority_tasks}

def daily_tasks_summary():
    today = datetime.now().strftime("%Y-%m-%d")
    results = collection.query(n_results=10)
    tasks = [task for task in results.get("documents", []) if task.get("due_date") == today]
    return {"tasks_due_today": tasks}

def delete_task(task):
    collection.delete(ids=[str(hash(task))])
    return {"message": "Task deleted successfully."}

# Long-Term Memory in ChromaDB
def remember_interaction(text, category="general"):
    collection.add(ids=[str(hash(text))], documents=[text], metadatas=[{"category": category}])
    return {"message": "Memory stored successfully."}

def search_memory(query, category=None):
    filters = {"category": category} if category else {}
    results = collection.query(query_texts=[query], n_results=5, where=filters)
    if results and "documents" in results and results["documents"]:
        return {"memories": results["documents"]}
    else:
        return {"error": "No relevant memories found."}

# FastAPI Web App
app = FastAPI()

@app.get("/list_dropbox_files")
def get_dropbox_files():
    return list_dropbox_files()

@app.get("/multi_summarize_dropbox_docs")
def get_multi_summarized_docs():
    return multi_summarize_dropbox_docs()

@app.get("/extract_key_points")
def get_key_points(text: str):
    return extract_key_points(text)

@app.post("/add_task")
def create_task(task: str, due_date: str, priority: str="medium"):
    return add_task(task, due_date, priority)

@app.get("/list_tasks")
def retrieve_tasks():
    return list_tasks()

@app.get("/list_high_priority_tasks")
def retrieve_high_priority_tasks():
    return list_high_priority_tasks()

@app.get("/daily_tasks_summary")
def retrieve_daily_tasks():
    return daily_tasks_summary()

@app.delete("/delete_task")
def remove_task(task: str):
    return delete_task(task)

@app.post("/remember")
def store_memory(text: str, category: str="general"):
    return remember_interaction(text, category)

@app.get("/search_memory")
def retrieve_memory(query: str, category: str=None):
    return search_memory(query, category)

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 YunaGPT API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
