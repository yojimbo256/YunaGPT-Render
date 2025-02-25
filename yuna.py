import os
import json
from fastapi import FastAPI
import openai
import chromadb
from chromadb.utils import embedding_functions
from github import Github
import requests
import dropbox

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

# Fetch and categorize Dropbox files
def categorize_dropbox_files():
    files = list_dropbox_files()
    if "error" in files:
        return files
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Categorize the following file names into meaningful groups."},
                {"role": "user", "content": json.dumps(files["files"])}
            ]
        )
        return {"categories": response.choices[0].message.content}
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return {"error": "Error categorizing files."}

# Task Management in ChromaDB
def add_task(task, due_date):
    collection.add(ids=[str(hash(task))], documents=[task], metadatas=[{"due_date": due_date}])
    return {"message": "Task added successfully."}

def list_tasks():
    results = collection.query(n_results=10)
    if results and "documents" in results:
        return {"tasks": results["documents"]}
    else:
        return {"error": "No tasks found."}

def delete_task(task):
    collection.delete(ids=[str(hash(task))])
    return {"message": "Task deleted successfully."}

# Long-Term Memory in ChromaDB
def remember_interaction(text):
    collection.add(ids=[str(hash(text))], documents=[text])
    return {"message": "Memory stored successfully."}

def recall_memory(query):
    results = collection.query(query_texts=[query], n_results=5)
    if results and "documents" in results:
        return {"memories": results["documents"]}
    else:
        return {"error": "No relevant memories found."}

# OpenAI API Chat Memory
conversation_history = []

def chat_with_yuna(prompt):
    global conversation_history
    conversation_history.append({"role": "user", "content": prompt})
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation_history
    )
    
    reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply})
    return reply

# FastAPI Web App
app = FastAPI()

@app.get("/")
def home():
    return {"message": "YunaGPT API is running!"}

@app.get("/ask")
def ask_yuna(query: str):
    response = chat_with_yuna(query)
    return {"response": response}

@app.get("/list_dropbox_files")
def get_dropbox_files():
    return list_dropbox_files()

@app.get("/categorize_dropbox_files")
def get_categorized_files():
    return categorize_dropbox_files()

@app.post("/add_task")
def create_task(task: str, due_date: str):
    return add_task(task, due_date)

@app.get("/list_tasks")
def retrieve_tasks():
    return list_tasks()

@app.delete("/delete_task")
def remove_task(task: str):
    return delete_task(task)

@app.post("/remember")
def store_memory(text: str):
    return remember_interaction(text)

@app.get("/recall")
def retrieve_memory(query: str):
    return recall_memory(query)

@app.get("/debug_routes")
def debug_routes():
    """Debug endpoint to list registered routes."""
    routes = [route.path for route in app.routes]
    print(f"DEBUG: Registered Routes -> {routes}")  # Logs routes during startup
    return {"routes": routes}

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 YunaGPT API has started successfully on Render!")

# Run FastAPI with Uvicorn (ensure correct port binding)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
