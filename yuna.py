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

# Corrected Dropbox file path
DROPBOX_FOLDER_PATH = "/Apps/YunaGPT-Storage/yuna-docs/"

# Fetch latest notes from Dropbox and summarize them
def fetch_and_summarize_dropbox_notes():
    """Fetches the latest text document from Dropbox and returns a structured summary."""
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
        
        # Store summary in memory
        store_summary(latest_file, summary)
        
        return {"file": latest_file, "summary": summary}
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

# Store summary in memory
def store_summary(file_name, summary):
    """Stores the summarized document in memory."""
    collection.add(
        ids=[str(hash(file_name))],
        documents=[summary],
        metadatas=[{"file_name": file_name, "timestamp": datetime.now().strftime("%Y-%m-%d")}]
    )
    print(f"Stored summary for {file_name} in memory.")

# Search stored summaries
def search_summaries(query):
    """Retrieves stored summaries that match a query."""
    results = collection.query(query_texts=[query], n_results=5)
    return {"matching_summaries": results.get("documents", [])}

# FastAPI Web App
app = FastAPI()

@app.get("/fetch_latest_notes_with_summary")
def get_latest_notes_with_summary():
    """Publicly accessible endpoint to fetch the latest Dropbox notes and their summary."""
    return fetch_and_summarize_dropbox_notes()

@app.get("/recall_summaries")
def recall_summaries():
    """Retrieve stored summaries from memory."""
    results = collection.query(n_results=10)
    return {"stored_summaries": results.get("documents", [])}

@app.get("/search_summaries")
def search_stored_summaries(query: str):
    """Search stored summaries by keyword."""
    return search_summaries(query)

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 YunaGPT API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
