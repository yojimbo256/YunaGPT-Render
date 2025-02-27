from flask import Flask, render_template, request, jsonify
import requests
from flask_cors import CORS

# Yuna API Base URL (Running on Mac Mini)
YUNA_API = "http://192.168.1.211:8000"

app = Flask(__name__)
CORS(app)  # Enable CORS globally

@app.route('/')
def home():
    return render_template("index.html")

# Fetch Memory
@app.route('/fetch_memory', methods=['GET'])
def fetch_memory():
    try:
        response = requests.get(f"{YUNA_API}/fetch_yuna_memory")
        response.raise_for_status()  # Raise an error for HTTP errors
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch memory: {str(e)}"}), 500

# Add Memory Entry
@app.route('/add_memory', methods=['POST'])
def add_memory():
    data = request.json
    payload = {"new_memory": data.get("memory", ""), "category": data.get("category", "general")}
    try:
        response = requests.post(f"{YUNA_API}/update_yuna_memory", json=payload)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to add memory: {str(e)}"}), 500

# Fetch Tasks
@app.route('/fetch_tasks', methods=['GET'])
def fetch_tasks():
    try:
        response = requests.get(f"{YUNA_API}/fetch_tasks")
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch tasks: {str(e)}"}), 500

# Add Task
@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.json
    payload = {"task": data.get("task", "")}
    try:
        response = requests.post(f"{YUNA_API}/add_task", json=payload)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to add task: {str(e)}"}), 500

# Generate Scheduled Summary
@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    try:
        response = requests.post(f"{YUNA_API}/generate_scheduled_summary")
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to generate summary: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
