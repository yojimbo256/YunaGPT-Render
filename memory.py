import sqlite3
from typing import List, Dict

DB_PATH = "yuna_memory.db"

def get_db_connection():
    """Creates and returns a new database connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """Creates the conversations table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def store_conversation(user_message: str, ai_response: str):
    """Saves a conversation to SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (user_message, ai_response) VALUES (?, ?)",
        (user_message, ai_response),
    )
    conn.commit()
    conn.close()

def get_recent_conversations(limit: int = 10) -> List[Dict[str, str]]:
    """Retrieves the most recent conversations from SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_message, ai_response, timestamp FROM conversations ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    data = cursor.fetchall()
    conn.close()
    return [{"user": row["user_message"], "yuna": row["ai_response"], "timestamp": row["timestamp"]} for row in data]

def delete_old_conversations(keep_latest: int = 100):
    """Deletes old conversations to maintain database efficiency."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM conversations WHERE id NOT IN (SELECT id FROM conversations ORDER BY timestamp DESC LIMIT ?)",
        (keep_latest,)
    )
    conn.commit()
    conn.close()

# Initialize the database when imported
initialize_db()
