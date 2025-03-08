from flask import Flask, render_template, request, jsonify
from memory import store_conversation, get_recent_conversations
import openai  # Replace this with your AI model integration

app = Flask(__name__)

# Configure OpenAI API Key (Replace with actual API key)
OPENAI_API_KEY = "your_openai_api_key_here"
openai.api_key = OPENAI_API_KEY

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"response": "Please enter a message."})

    # Generate AI response using OpenAI (or another AI model)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Replace with the appropriate model
            messages=[{"role": "system", "content": "You are Yuna, a helpful AI assistant."},
                      {"role": "user", "content": user_message}]
        )
        ai_response = response["choices"][0]["message"]["content"]
    except Exception as e:
        ai_response = "Sorry, I encountered an error generating a response."
        print(f"AI Error: {e}")
    
    # Store conversation in memory
    store_conversation(user_message, ai_response)
    
    return jsonify({"response": ai_response})

@app.route('/history', methods=['GET'])
def history():
    conversations = get_recent_conversations(limit=5)
    return jsonify({"conversations": conversations})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
