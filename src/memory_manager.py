import os
import sqlite3
import zlib
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- V9: Local SQLite Database Configuration ---
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'kim_young_mi_memory.db')
db_conn = None

def initialize_memory():
    """
    Initializes the connection to the local SQLite database and creates tables if they don't exist.
    """
    global db_conn
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = db_conn.cursor()

        # --- V9: Expanded Memory Tables ---
        # A simple key-value store for metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # A table for storing conversation history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                compressed_history BLOB
            )
        ''')
        # A table for storing learned facts from her curiosity
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_facts (
                topic TEXT PRIMARY KEY,
                data TEXT,
                timestamp INTEGER
            )
        ''')
        # A table for words she knows to prevent re-learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS known_words (
                word TEXT PRIMARY KEY
            )
        ''')

        db_conn.commit()
        print("Local memory database initialized successfully.")
        return True
    except Exception as e:
        print(f"Failed to initialize SQLite database: {e}")
        return False

# --- Conversation and Metadata Functions (Simplified for brevity) ---
def save_conversation(conversation_history):
    if not db_conn: return
    try:
        history_json = json.dumps(conversation_history)
        compressed_history = zlib.compress(history_json.encode('utf-8'))
        cursor = db_conn.cursor()
        cursor.execute("INSERT INTO conversations (timestamp, compressed_history) VALUES (?, ?)",
                       (int(time.time()), compressed_history))
        db_conn.commit()
    except Exception as e:
        print(f"Error saving conversation: {e}")

def retrieve_conversation():
    if not db_conn: return []
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT compressed_history FROM conversations ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return json.loads(zlib.decompress(row[0]).decode('utf-8'))
        return []
    except Exception as e:
        print(f"Error retrieving conversation: {e}")
        return []

def save_metadata(key, value):
    if not db_conn: return
    cursor = db_conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", (key, str(value)))
    db_conn.commit()

def retrieve_metadata(key):
    if not db_conn: return None
    cursor = db_conn.cursor()
    cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else None

# --- V9: Autonomous Learning Functions ---
def add_known_word(word):
    """Adds a new word to the known_words table."""
    save_metadata(f"known_word_{word.lower()}", "1")

def is_word_known(word):
    """Checks if a word is in the known_words metadata table."""
    return retrieve_metadata(f"known_word_{word.lower()}") is not None

def add_learned_fact(topic, data):
    """Adds a new learned fact to the database."""
    if not db_conn: return
    try:
        cursor = db_conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO learned_facts (topic, data, timestamp) VALUES (?, ?, ?)",
                       (topic.lower(), data, int(time.time())))
        db_conn.commit()
        add_known_word(topic) # Add the topic itself to known words
        print(f"Successfully learned and stored a new fact about '{topic}'.")
    except Exception as e:
        print(f"Error saving learned fact: {e}")

def get_all_learned_facts():
    """Retrieves all learned facts from the database."""
    if not db_conn: return ""
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT topic, data FROM learned_facts ORDER BY timestamp DESC")
        facts = cursor.fetchall()
        # Format facts into a string for the AI's context
        return "\n".join([f"- {topic.title()}: {data}" for topic, data in facts])
    except Exception as e:
        print(f"Error retrieving learned facts: {e}")
        return ""

if __name__ == '__main__':
    print("--- Testing memory_manager.py (V9 Autonomous Learning) ---")
    if initialize_memory():
        # Test fact learning
        test_topic = "Clove"
        test_fact = "Clove is the latest Controller agent in Valorant."
        add_learned_fact(test_topic, test_fact)

        # Test word knowledge
        assert is_word_known("Clove") == True
        assert is_word_known("Jett") == False # Assuming Jett hasn't been learned yet

        # Test fact retrieval
        all_facts = get_all_learned_facts()
        print("\nAll Learned Facts:")
        print(all_facts)
        assert test_topic in all_facts

        print("\n--- All V9 memory tests passed! ---")
        db_conn.close()