import sqlite3
from datetime import datetime, timedelta
from rapidfuzz import fuzz

# === ✅ Database Connection (Context Manager) ===
def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect("yuna_memory.db")
    conn.row_factory = sqlite3.Row
    return conn

# === ✅ Initialize Memory Table ===
def init_memory_db():
    """Ensure the conversations table exists with correct columns."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT,
                ai_response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

# === ✅ Store Conversation in Memory (With Summarization) ===
def store_conversation(user_message: str, ai_response: str):
    """Store a new user message and AI response, summarizing if needed."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Summarize if response is too long
        if len(ai_response) > 500:
            ai_response = ai_response[:500] + "... (truncated)"
        
        cursor.execute(
            "INSERT INTO conversations (user_message, ai_response) VALUES (?, ?)",
            (user_message, ai_response),
        )
        conn.commit()

# === ✅ Retrieve Recent Conversations (Prioritizing User Input Length) ===
def get_recent_conversations(limit: int = 10):
    """Retrieve the last N conversations, prioritizing longer user inputs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT user_message, ai_response, timestamp FROM conversations
            ORDER BY LENGTH(user_message) DESC, timestamp DESC LIMIT ?""",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

# === ✅ Delete Old Conversations (Keep Latest N Entries) ===
def delete_old_conversations(keep_latest: int = 100):
    """Deletes older records but keeps the latest N conversations."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM conversations 
            WHERE id NOT IN (
            SELECT id FROM conversations 
            ORDER BY timestamp DESC 
            LIMIT ?
        )
        """,
        (keep_latest,)
        )
        conn.commit()

# === ✅ Fuzzy Search in Memory ===
def search_conversation(query: str, limit: int = 5):
    """Search past conversations using fuzzy matching."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_message, ai_response, timestamp FROM conversations")
        all_conversations = cursor.fetchall()
        
        # Filter by similarity threshold (70% match)
        results = [
            dict(row)
            for row in all_conversations
            if fuzz.partial_ratio(query, row["user_message"]) > 70
        ][:limit]
        
        return results

# === ✅ Initialize DB on Import ===
init_memory_db()
