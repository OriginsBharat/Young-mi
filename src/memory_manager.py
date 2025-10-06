import os
import sqlite3
import zlib
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- V6: Local SQLite Database Configuration ---
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'kim_young_mi_memory.db')
db_conn = None

def initialize_memory():
    """
    Initializes the connection to the local SQLite database and creates tables if they don't exist.
    """
    global db_conn
    try:
        # Ensure the 'data' directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        db_conn = sqlite3.connect(DB_PATH)
        cursor = db_conn.cursor()

        # Create tables
        # A simple key-value store for metadata like timestamps and learned insights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # A table for storing conversation history sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                compressed_history BLOB
            )
        ''')

        db_conn.commit()
        print("Local memory database initialized successfully.")
        return True
    except Exception as e:
        print(f"Failed to initialize SQLite database: {e}")
        return False

def save_conversation(conversation_history):
    """Compresses conversation history and saves it to the local SQLite database."""
    if not db_conn: return
    print("Saving conversation to local memory...")
    try:
        history_json = json.dumps(conversation_history)
        compressed_history = zlib.compress(history_json.encode('utf-8'))

        cursor = db_conn.cursor()
        cursor.execute("INSERT INTO conversations (timestamp, compressed_history) VALUES (?, ?)",
                       (int(time.time()), compressed_history))
        db_conn.commit()
        print("Successfully saved compressed conversation.")
    except Exception as e:
        print(f"Error saving conversation to local memory: {e}")

def retrieve_conversation():
    """Retrieves and decompresses the most recent conversation from the local database."""
    if not db_conn: return []
    print("Retrieving conversation from local memory...")
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT compressed_history FROM conversations ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            decompressed_json = zlib.decompress(row[0]).decode('utf-8')
            print("Successfully retrieved and decompressed conversation.")
            return json.loads(decompressed_json)
        return []
    except Exception as e:
        print(f"Error retrieving conversation from local memory: {e}")
        return []

def save_metadata(key, value):
    """Saves a key-value pair to the metadata table."""
    if not db_conn: return
    try:
        cursor = db_conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", (key, value))
        db_conn.commit()
    except Exception as e:
        print(f"Error saving metadata '{key}': {e}")

def retrieve_metadata(key):
    """Retrieves a value from the metadata table by key."""
    if not db_conn: return None
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"Error retrieving metadata '{key}': {e}")
        return None

if __name__ == '__main__':
    print("--- Testing memory_manager.py (SQLite Version) ---")
    if initialize_memory():
        # Test conversation
        test_history = [{"role": "user", "content": f"Test message at {time.time()}"}]
        save_conversation(test_history)
        retrieved = retrieve_conversation()
        print(f"Retrieved History: {retrieved}")
        assert test_history == retrieved

        # Test metadata
        save_metadata("last_seen", int(time.time()))
        retrieved_ts = retrieve_metadata("last_seen")
        print(f"Retrieved timestamp: {retrieved_ts}")
        assert isinstance(int(retrieved_ts), int)

        test_insights = "Learned that the user likes SQLite."
        save_metadata("learned_personality", test_insights)
        retrieved_insights = retrieve_metadata("learned_personality")
        print(f"Retrieved insights: {retrieved_insights}")
        assert test_insights == retrieved_insights

        print("\n--- All SQLite tests passed! ---")
        db_conn.close()