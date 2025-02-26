# YunaGPT-Render

## Overview
Yuna is an AI-powered personal assistant designed to help manage files, tasks, and memories efficiently using **Dropbox, ChromaDB, and OpenAI**. It automates note-taking, project tracking, and scheduled summaries while allowing easy recall of past interactions.

## Features

### 🗂 **Dropbox File Management**
- **Fetch Latest Notes:** Retrieve the most recent notes and summaries.
  ```sh
  curl "https://yunagpt-render.onrender.com/fetch_latest_notes_with_summary_and_tags"
  ```
- **Write a New File to Dropbox:**
  ```sh
  curl -X POST "https://yunagpt-render.onrender.com/write_to_dropbox" \
       -H "Content-Type: application/json" \
       -d '{"file_name": "tasks.txt", "content": "Complete final edits on Yuna."}'
  ```
- **Update an Existing File in Dropbox:**
  ```sh
  curl -X POST "https://yunagpt-render.onrender.com/update_dropbox_file" \
       -H "Content-Type: application/json" \
       -d '{"file_name": "tasks.txt", "update_content": "Added another task: Review AI model improvements."}'
  ```

### 📋 **Task Management**
- **Check Upcoming Tasks:**
  ```sh
  curl "https://yunagpt-render.onrender.com/check_upcoming_tasks"
  ```
- **Auto-Delete Old Tasks & Projects:**
  ```sh
  curl -X POST "https://yunagpt-render.onrender.com/auto_delete_old_entries"
  ```

### 📊 **Reports & Summaries**
- **Generate a Daily Report:**
  ```sh
  curl -X POST "https://yunagpt-render.onrender.com/generate_scheduled_summary"
  ```
- **Structured Summaries of Dropbox Files:**
  ```sh
  curl "https://yunagpt-render.onrender.com/structured_summarize_dropbox_doc?file=notes.txt"
  ```

### 🧠 **Memory Recall & AI Contextual Awareness**
- **Search Memory for Context:**
  ```sh
  curl "https://yunagpt-render.onrender.com/search_memory?query=project"
  ```
- **Retrieve Related Memories:**
  ```sh
  curl "https://yunagpt-render.onrender.com/contextual_memory_recall?query=project"
  ```
- **Summarize Yuna's Stored Memories:**
  ```sh
  curl "https://yunagpt-render.onrender.com/summarize_yuna_memory"
  ```
- **Delete Memories Older than 30 Days:**
  ```sh
  curl -X POST "https://yunagpt-render.onrender.com/delete_old_memories" \
       -H "Content-Type: application/json" \
       -d '{"days": 30}'
  ```

### 🛠 **Automated Workflows & Background Automation**
- **Automate Workflow with Background Scripts**
  - Set up a background automation script to trigger tasks based on ChatGPT usage:
    ```sh
    @reboot python3 "/Users/yojimbo256/Python Scripts/yuna_automation.py" &
    0 */3 * * * python3 "/Users/yojimbo256/Python Scripts/yuna_automation.py" >> /Users/yojimbo256/yuna_log.txt 2>&1 &
    ```

## Installation & Setup
### 🚀 **Running Yuna Locally**
1. **Clone the Repository**
   ```sh
   git clone https://github.com/yojimbo256/YunaGPT-Render.git
   cd YunaGPT-Render
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
DROPBOX_ACCESS_TOKEN=<your_dropbox_token>
PORT=8000
```

## Roadmap 🚀
- [ ] Auto-delete outdated tasks & projects.
- [ ] Sync tasks between Dropbox & ChromaDB.
- [ ] Enable version control for Dropbox files.
- [ ] Integrate real-time AI assistance via voice commands.

## License 📜
MIT License. See `LICENSE` for more details.

