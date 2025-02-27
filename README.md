# Yuna AI Assistant

## Overview
Yuna is an AI-powered personal assistant designed to help manage files, tasks, and memories efficiently using **SQLite, ChromaDB, and OpenAI**. It automates note-taking, project tracking, and scheduled summaries while allowing easy recall of past interactions.

## Features

### 🗂 **File & Memory Management**
- **Fetch Latest Memories:** Retrieve the most recent stored memories.
  ```sh
  curl "http://127.0.0.1:8000/fetch_yuna_memory"
  ```
- **Store a New Memory Entry:**
  ```sh
  curl -X POST "http://127.0.0.1:8000/update_yuna_memory" \
       -H "Content-Type: application/json" \
       -d '{"new_memory": "Meeting notes", "category": "work", "permanent": true}'
  ```
- **Search Memory Using Fuzzy Matching:**
  ```sh
  curl "http://127.0.0.1:8000/search_yuna_memory?query=project"
  ```
- **Delete Old Non-Permanent Memories:**
  ```sh
  curl -X POST "http://127.0.0.1:8000/delete_old_memories" \
       -H "Content-Type: application/json" \
       -d '{"days": 30}'
  ```

### 📋 **Task Management**
- **Check Stored Tasks:**
  ```sh
  curl "http://127.0.0.1:8000/fetch_tasks"
  ```
- **Add a Task:**
  ```sh
  curl -X POST "http://127.0.0.1:8000/add_task" \
       -H "Content-Type: application/json" \
       -d '{"task": "Finish Yuna documentation", "priority": "high", "due_date": "2025-03-01"}'
  ```
- **Update Task Status:**
  ```sh
  curl -X POST "http://127.0.0.1:8000/update_task_status" \
       -H "Content-Type: application/json" \
       -d '{"index": 0, "new_status": "completed"}'
  ```

### 📊 **Reports & Summaries**
- **Generate a Daily Report:**
  ```sh
  curl -X POST "http://127.0.0.1:8000/generate_scheduled_summary"
  ```
- **Retrieve Logs:**
  ```sh
  curl "http://127.0.0.1:8000/logs"
  ```

### 🛠 **Automated Workflows & Background Automation**
- **Automate Workflow with Startup Script**
  - Set up Yuna to start automatically using login items:
    ```sh
    chmod +x ~/start_yuna.sh
    ```
  - Add `~/start_yuna.sh` to macOS login items.

## Installation & Setup
### 🚀 **Running Yuna Locally**
1. **Clone the Repository**
   ```sh
   git clone https://github.com/yojimbo256/Yuna-AI.git
   cd Yuna-AI
   ```
2. **Install Dependencies**
   ```sh
   pip install -r requirements.txt
   ```
3. **Run the API Server**
   ```sh
   uvicorn yuna:app --host 0.0.0.0 --port 8000
   ```

### 🛠 **Environment Variables**
Set the following environment variables:
```
OPENAI_API_KEY=<your_openai_api_key>
GITHUB_ACCESS_TOKEN=<your_github_token>
PORT=8000
```

## Roadmap 🚀
- [ ] Improve auto-start mechanism.
- [ ] Enhance memory summarization before deletion.
- [ ] Implement SQLite query optimization for faster recall.
- [ ] Add voice command support.

## License 📜
MIT License. See `LICENSE` for more details.
