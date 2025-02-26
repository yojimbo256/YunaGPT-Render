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

# Define Pydantic model for JSON requests
class DropboxRequest(BaseModel):
    file_name: str
    content: str

# List of Active Projects
PROJECTS_MD = """# Active Projects\n\n## 1️⃣ Yuna – AI Personal Assistant\n✅ Automates Dropbox file management, memory recall, and task tracking.\n✅ Reads & writes to Dropbox.\n✅ Stores and retrieves contextual memory in ChromaDB.\n\n## 2️⃣ DevSecOps AI\n✅ AI-driven cybersecurity automation tool.\n✅ Automates compliance & vulnerability detection.\n\n## 3️⃣ Soteria – Cybersecurity Compliance System\n✅ AI-driven compliance automation & vulnerability management.\n✅ Scans for vulnerabilities (CVE detection).\n\n## 4️⃣ AI-Powered Task & Workflow Automation\n✅ AI-assisted task scheduling and workflow automation.\n✅ Integration with Dropbox & Slack.\n\n## 5️⃣ PhD Research – AI in DevSecOps\n✅ Researching AI-driven compliance automation.\n✅ Building AI-powered threat detection.\n\n## 6️⃣ Custom AI Models\n✅ Development of custom AI models for security and automation.\n✅ Deployment on enterprise infrastructure.\n"""

PROJECTS_JSON = json.dumps({
    "projects": [
        {
            "name": "Yuna – AI Personal Assistant",
            "description": "Automates Dropbox file management, memory recall, and task tracking.",
            "capabilities": ["Reads & writes to Dropbox", "Stores and retrieves memory in ChromaDB"]
        },
        {
            "name": "DevSecOps AI",
            "description": "AI-driven cybersecurity automation tool.",
            "capabilities": ["Automates compliance & vulnerability detection"]
        },
        {
            "name": "Soteria – Cybersecurity Compliance System",
            "description": "AI-driven compliance automation & vulnerability management.",
            "capabilities": ["Scans for vulnerabilities (CVE detection)"]
        },
        {
            "name": "AI-Powered Task & Workflow Automation",
            "description": "AI-assisted task scheduling and workflow automation.",
            "capabilities": ["Integration with Dropbox & Slack"]
        },
        {
            "name": "PhD Research – AI in DevSecOps",
            "description": "Researching AI-driven compliance automation & threat detection.",
            "capabilities": ["Building AI-powered threat detection"]
        },
        {
            "name": "Custom AI Models",
            "description": "Development of custom AI models for security and automation.",
            "capabilities": ["Deployment on enterprise infrastructure"]
        }
    ]
}, indent=4)

# Write projects to Dropbox
def write_projects_to_dropbox():
    """Writes both Markdown and JSON project lists to Dropbox."""
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        dbx.files_upload(PROJECTS_MD.encode("utf-8"), f"{DROPBOX_FOLDER_PATH}projects.md", mode=dropbox.files.WriteMode("overwrite"))
        dbx.files_upload(PROJECTS_JSON.encode("utf-8"), f"{DROPBOX_FOLDER_PATH}projects.json", mode=dropbox.files.WriteMode("overwrite"))
        return {"message": "Projects successfully written to Dropbox."}
    except Exception as e:
        print(f"Dropbox Write Error: {e}")
        return {"error": str(e)}

# FastAPI Web App
app = FastAPI()

@app.post("/write_projects_to_dropbox")
def save_projects():
    """Writes project details to Dropbox."""
    return write_projects_to_dropbox()

@app.on_event("startup")
async def startup_event():
    print("\U0001F680 Yuna API has started successfully on Render!")

# Run FastAPI with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=True)
