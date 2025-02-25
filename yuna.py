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

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Initialize ChromaDB for Persistent Memory
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("yuna_knowledge")

DROPBOX_FILE_PATH = "/yuna-docs/notes.txt"  # Path to your document in Dropbox

def fetch_dropbox_doc():
    """Fetches a text document from Dropbox."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        _, response = dbx.files_download(DROPBOX_FILE_PATH)
        return {"document_content": response.content.decode("utf-8")}
    except dropbox.exceptions.ApiError as e:
        return {"error": str(e)}

# Initialize GitHub API Client
try:
    g = Github(GITHUB_ACCESS_TOKEN)
    repo_name = "yojimbo256/YunaGPT-Render"  # Ensure this is correct
    repo = g.get_repo(repo_name)
except Exception as e:
    print(f"GitHub API Error: {e}")
    repo = None

def fetch_github_issues():
    """Fetches open GitHub issues from the repository."""
    if not repo:
        return {"error": "GitHub repository not found or API token is incorrect."}
    
    try:
        issues = repo.get_issues(state="open")
        return [{"title": issue.title, "url": issue.html_url} for issue in issues]
    except Exception as e:
        return {"error": str(e)}

# Store Knowledge in ChromaDB
def store_knowledge(title, content):
    collection.add(embedding=embedding_functions.openai(), documents=[content], metadatas=[{"title": title}])

def retrieve_knowledge(query):
    return collection.query(query_texts=[query], n_results=5)

# OpenAI API Chat Memory
conversation_history = []

def chat_with_yuna(prompt):
    global conversation_history
    conversation_history.append({"role": "user", "content": prompt})
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation_history
    )
    
    reply = response["choices"][0]["message"]["content"]
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

@app.get("/fetch_dropbox_doc")
def get_dropbox_doc():
    """Fetches a document from Dropbox."""
    content = fetch_dropbox_doc()
    return content

@app.get("/fetch_github_issues")
def get_github_issues():
    return fetch_github_issues()

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
