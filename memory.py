import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict
from rapidfuzz import process

# Set local storage directory (only memories sync to iCloud)
YUNA_MEMORY_PATH = "/usr/local/yuna/data/"
SHORT_TERM_MEMORY_FILE = os.path.join(YUNA_MEMORY_PATH, "short_term_memory.json")
LONG_TERM_MEMORY_DB = os.path.join(YUNA_MEMORY_PATH, "long_term_memory.db")

# Ensure the storage directory exists
os.makedirs(YUNA_MEMORY_PATH, exist_ok=True)

# Ensure database is initialized at startup
def ensure_db_initialized():
    """Ensures the database and table are correctly initialized."""
    conn = sqlite3.connect(LONG_TERM_MEMORY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            category TEXT,
            content TEXT,
            permanent INTEGER DEFAULT 0
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON memory (category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memory (timestamp)")
    conn.commit()
    conn.close()

# Call the function at the beginning of the script
ensure_db_initialized()

# Function to store short-term memory
def save_short_term_memory(data: Dict):
    with open(SHORT_TERM_MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Function to load short-term memory
def load_short_term_memory() -> Dict:
    if os.path.exists(SHORT_TERM_MEMORY_FILE):
        with open(SHORT_TERM_MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}

# Function to store long-term memory
def save_long_term_memory(content: str, category: str, permanent: bool = False):
    conn = sqlite3.connect(LONG_TERM_MEMORY_DB)
    cursor = conn.cursor()

    # ✅ Enable WAL mode for durability
    cursor.execute("PRAGMA journal_mode=WAL;")

    cursor.execute("""
        INSERT INTO memory (timestamp, category, content, permanent) 
        VALUES (?, ?, ?, ?)
    """, (datetime.now().isoformat(), category, content, int(permanent)))
    
    conn.commit()  # ✅ Force write before closing
    cursor.close()
    conn.close()

    print("✅ Successfully saved memory to long-term database.")

# ✅ FIXED: Fuzzy Search for Memory Retrieval
def retrieve_memory(query: str, limit: int = 5) -> List[Dict]:
    conn = sqlite3.connect(LONG_TERM_MEMORY_DB)
    cursor = conn.cursor()

    # Get all categories
    cursor.execute("SELECT DISTINCT category FROM memory")
    categories = [row[0] for row in cursor.fetchall()]
    
    # If no categories exist, return empty
    if not categories:
        conn.close()
        return []
    
    # Find closest category match
    matched_category, score = process.extractOne(query, categories)

    # DEBUG: Print the best match
    print(f"🔍 Fuzzy search for '{query}' matched category: '{matched_category}' (Score: {score})")

    if score > 60:  # Set a confidence threshold
        cursor.execute("""
            SELECT timestamp, category, content FROM memory 
            WHERE category = ? 
            ORDER BY timestamp DESC LIMIT ?
        """, (matched_category, limit))
        rows = cursor.fetchall()
        conn.close()
        return [{"timestamp": row[0], "category": row[1], "content": row[2]} for row in rows]

    conn.close()
    return []  # No match found

# Function to delete old memories (excluding permanent ones) with summarization
def delete_old_memories(days: int = 30):
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(LONG_TERM_MEMORY_DB)
    cursor = conn.cursor()
    
    # Fetch memories to be deleted
    cursor.execute("SELECT category, content FROM memory WHERE timestamp < ? AND permanent = 0", (cutoff_date,))
    old_memories = cursor.fetchall()
    
    if old_memories:
        # Summarize before deleting
        summary = f"Summary of deleted memories:\n" + "\n".join([f"{cat}: {content}" for cat, content in old_memories])
        save_long_term_memory(summary, "summarized_deletions", permanent=True)

    # Delete old, non-permanent memories
    cursor.execute("DELETE FROM memory WHERE timestamp < ? AND permanent = 0", (cutoff_date,))
    conn.commit()
    conn.close()

# Function to manually mark memory as permanent
def mark_memory_permanent(content: str):
    conn = sqlite3.connect(LONG_TERM_MEMORY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE memory SET permanent = 1 WHERE content = ?
    """, (content,))
    conn.commit()
    conn.close()
