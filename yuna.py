from fastapi import FastAPI
import openai
import chromadb
from chromadb.utils import embedding_functions
from googleapiclient.discovery import build
from github import Github
import os

# Load API Keys (Set these in Render Environment Variables)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_DOCS_API_KEY = os.getenv("GOOGLE_DOCS_API_KEY")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Initialize ChromaDB for Memory
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("yuna_knowledge")

# Google Docs API Setup
DOC_ID = "your_google_doc_id"
docs_service = build("docs", "v1", developerKey=GOOGLE_DOCS_API_KEY)

def fetch_google_doc():
    document = docs_service.documents().get(documentId=DOC_ID).execute()
    return document.get("body").get("content")

# GitHub API Setup
g = Github(GITHUB_ACCESS_TOKEN)
repo = g.get_repo("your_github_repo")

def fetch_github_issues():
    return repo.get_issues(state="open")

# Store Knowledge in ChromaDB
def store_knowledge(title, content):
    collection.add(embedding=embedding_functions.openai(), documents=[content], metadatas=[{"title": title}])

def retrieve_knowledge(query):
    return collection.query(query_texts=[query], n_results=5)

# FastAPI Web App
app = FastAPI()

@app.get("/")
def home():
    return {"message": "YunaGPT API is running!"}

@app.get("/ask")
def ask_yuna(query: str):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": query}]
    )
    return {"response": response["choices"][0]["message"]["content"]}
