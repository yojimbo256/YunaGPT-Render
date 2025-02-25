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

# Corrected Dropbox file path
DROPBOX_FOLDER_PATH = "/Apps/YunaGPT-Storage/yuna-docs/"

# Fetch latest notes from Dropbox, summarize, and tag them
def fetch_summarize_tag_dropbox_notes():
    """Fetches the latest text document from Dropbox, summarizes, and tags it."""
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
        
        return {"file": latest_file, "summary": summary, "tags": tags}
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

# Retrieve upcoming and overdue tasks
def check_upcoming_tasks():
    """Retrieves tasks due within the next 3 days."""
    upcoming_tasks = []
    
    # Query for stored tasks
    try:
        results = collection.query(n_results=100)
    except Exception as e:
        print(f"ChromaDB Query Error: {e}")
        return {"error": "Failed to retrieve tasks from database."}
    
    # Handle empty query results
    if not results or "metadatas" not in results or not results["metadatas"]:
        print("No tasks found in the database.")
        return {"upcoming_tasks": "No tasks found in the database."}
    
    for task in results["metadatas"]:
        if "due_date" in task and isinstance(task["due_date"], str):
            try:
                due_date = datetime.strptime(task["due_date"], "%Y-%m-%d")
                if due_date <= datetime.now() + timedelta(days=3):
                    upcoming_tasks.append(task)
            except ValueError:
                print(f"Invalid date format in task: {task['due_date']}")
                continue  # Skip invalid dates
        else:
            print(f"Skipping task due to missing 'due_date' field: {task}")
    
    return {"upcoming_tasks": upcoming_tasks if upcoming_tasks else "No upcoming tasks found."}

# Context-aware memory recall
def contextual_memory_recall(query):
    """Retrieves stored memories relevant to the query."""
    results = collection.query(query_texts=[query], n_results=5)
    if results and "documents" in results and results["documents"]:
        return {"related_memories": results["documents"]}
    else:
        return {"error": "No relevant memories found. Try broadening your query."}

# FastAPI Web App
app = FastAPI()

@app.get("/fetch_latest_notes_with_summary_and_tags")
def get_latest_notes_with_summary_and_tags():
    """Fetches, summarizes, and tags the latest Dropbox document."""
    return fetch_summarize_tag_dropbox_notes()

@app.get("/check_upcoming_tasks")
def get_upcoming_tasks():
    """Lists tasks due within the next 3 days."""
    return check_upcoming_tasks()

@app.get("/contextual_memory_recall")
def get_contextual_memory_recall(query: str):
    """Retrieves stored memories relevant to the query."""
    return contextual_memory_recall(query)

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 YunaGPT API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
