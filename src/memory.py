import sqlite3
from datetime import datetime, timedelta
from rapidfuzz import fuzz

DB_PATH = "data/database/yuna_memory.db"

# === ✅ Initialize SQLite Database
def init_db():
    """Ensure the database schema is correct."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            ai_response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# === ✅ Store Conversations
def store_conversation(user_message: str, ai_response: str):
    """Save user-AI conversation to SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (user_message, ai_response) VALUES (?, ?)", (user_message, ai_response))
    conn.commit()
    conn.close()

# === ✅ Fetch Recent Conversations
def get_recent_conversations(limit: int = 10):
    """Retrieve the latest N user-AI interactions from memory."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_message, ai_response, timestamp FROM conversations ORDER BY timestamp DESC LIMIT ?", (limit,))
    conversations = [{"user_message": row[0], "ai_response": row[1], "timestamp": row[2]} for row in cursor.fetchall()]
    conn.close()
    return conversations

# === ✅ Delete Old Conversations
def delete_old_conversations(keep_latest: int = 100):
    """Delete old conversations but keep the latest N records."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM conversations")
    count = cursor.fetchone()[0]

    if count > keep_latest:
        excess = count - keep_latest
        cursor.execute("DELETE FROM conversations WHERE id IN (SELECT id FROM conversations ORDER BY timestamp ASC LIMIT ?)", (excess,))
        conn.commit()
    
    conn.close()
