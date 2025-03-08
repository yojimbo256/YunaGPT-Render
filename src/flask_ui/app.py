from flask import Flask, render_template, request, jsonify
from src.memory import store_conversation, get_recent_conversations

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"response": "Please enter a message."})

    # Simulate a simple response (Replace with AI model later)
    ai_response = f"Yuna: {user_message[::-1]}"  # Reverse text as a placeholder response
    
    # Store conversation in memory
    store_conversation(user_message, ai_response)
    
    return jsonify({"response": ai_response})

@app.route('/history', methods=['GET'])
def history():
    conversations = get_recent_conversations(limit=5)
    return jsonify({"conversations": conversations})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
