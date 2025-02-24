import os
import json
from fastapi import FastAPI
import openai
import chromadb
from chromadb.utils import embedding_functions
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from github import Github

# Load API Keys from Render Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
GOOGLE_DOCS_CREDENTIALS = os.getenv("GOOGLE_DOCS_CREDENTIALS")

# Ensure GOOGLE_DOCS_CREDENTIALS is properly set
if not GOOGLE_DOCS_CREDENTIALS or GOOGLE_DOCS_CREDENTIALS.strip() == "":
    raise ValueError("GOOGLE_DOCS_CREDENTIALS environment variable is missing or improperly formatted!")

try:
    creds_dict = json.loads(GOOGLE_DOCS_CREDENTIALS)
    creds = Credentials.from_service_account_info(creds_dict)
except json.JSONDecodeError:
    raise ValueError("Failed to parse GOOGLE_DOCS_CREDENTIALS as JSON. Ensure it's stored correctly.")

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Initialize ChromaDB for Persistent Memory
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("yuna_knowledge")

# Initialize Google Docs API
docs_service = build("docs", "v1", credentials=creds)
DOC_ID = "your_google_doc_id"  # Replace with your actual Google Doc ID

def fetch_google_doc():
    document = docs_service.documents().get(documentId=DOC_ID).execute()
    return document.get("body").get("content")

# Initialize GitHub API Client
g = Github(GITHUB_ACCESS_TOKEN)
repo_name = "your_github_username/your_repo_name"  # Replace with your repo
repo = g.get_repo(repo_name)

def fetch_github_issues():
    """Fetches open GitHub issues from the repository."""
    issues = repo.get_issues(state="open")
    return [{"title": issue.title, "url": issue.html_url} for issue in issues]

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

@app.get("/fetch_google_doc")
def get_google_doc():
    content = fetch_google_doc()
    return {"document_content": content}

@app.get("/fetch_github_issues")
def get_github_issues():
    issues = fetch_github_issues()
    return {"github_issues": issues}
