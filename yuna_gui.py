from flask import Flask, render_template, request, jsonify
import requests
import os
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor
from flask_caching import Cache

# Load Yuna API Base URL from Environment Variables (Default: Mac Mini)
YUNA_API = os.getenv("YUNA_API", "http://192.168.1.211:8000")

app = Flask(__name__)
CORS(app)  # Enable CORS globally

# Configure caching (Memory-based, expires in 30 seconds)
cache = Cache(app, config={"CACHE_TYPE": "simple", "CACHE_DEFAULT_TIMEOUT": 30})

# ThreadPoolExecutor for Non-blocking Requests
executor = ThreadPoolExecutor(max_workers=4)

@app.route('/')
def home():
    return render_template("index.html")

# Fetch Memory (Cached)
@app.route('/fetch_memory', methods=['GET'])
@cache.cached(timeout=30)
def fetch_memory():
    try:
        response = requests.get(f"{YUNA_API}/fetch_yuna_memory", timeout=5)
        response.raise_for_status()  # Raise an error for HTTP errors
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch memory: {str(e)}"}), 500

# Add Memory Entry (Non-blocking)
@app.route('/add_memory', methods=['POST'])
def add_memory():
    data = request.json
    payload = {"new_memory": data.get("memory", ""), "category": data.get("category", "general")}

    def async_add_memory():
        try:
            response = requests.post(f"{YUNA_API}/update_yuna_memory", json=payload, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to add memory: {str(e)}"}

    executor.submit(async_add_memory)
    return jsonify({"message": "Memory update is being processed."})

# Fetch Tasks (Cached)
@app.route('/fetch_tasks', methods=['GET'])
@cache.cached(timeout=30)
def fetch_tasks():
    try:
        response = requests.get(f"{YUNA_API}/fetch_tasks", timeout=5)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch tasks: {str(e)}"}), 500

# Add Task with Priority & Due Date (Non-blocking)
@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.json
    payload = {
        "task": data.get("task", ""),
        "priority": data.get("priority", "normal"),
        "due_date": data.get("due_date", None),
        "status": "pending"
    }

    def async_add_task():
        try:
            response = requests.post(f"{YUNA_API}/add_task", json=payload, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to add task: {str(e)}"}

    executor.submit(async_add_task)
    return jsonify({"message": "Task is being processed."})

# Update Task Status
@app.route('/update_task', methods=['POST'])
def update_task():
    data = request.json
    payload = {"index": data.get("index"), "new_status": data.get("new_status")}

    try:
        response = requests.post(f"{YUNA_API}/update_task_status", json=payload, timeout=5)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to update task: {str(e)}"}), 500

# Generate Scheduled Summary (Non-blocking)
@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    def async_generate_summary():
        try:
            response = requests.post(f"{YUNA_API}/generate_scheduled_summary", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to generate summary: {str(e)}"}

    executor.submit(async_generate_summary)
    return jsonify({"message": "Summary generation is in progress."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
