import os
import requests
import zlib
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Pantry Configuration ---
PANTRY_ID = os.getenv("PANTRY_ID")
PANTRY_URL = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}"

# We will use different "baskets" (endpoints) for different data types
CONVERSATION_BASKET = "conversation_history"
METADATA_BASKET = "metadata"
LEARNED_FACTS_BASKET = "learned_facts"
KNOWN_WORDS_BASKET = "known_words"

def _pantry_put(basket_name, payload):
    """Helper function to send data to a Pantry basket."""
    if not PANTRY_ID: return False
    try:
        url = f"{PANTRY_URL}/basket/{basket_name}"
        headers = {'Content-Type': 'application/json'}
        response = requests.put(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"[ERROR] Could not save to Pantry basket '{basket_name}': {e}")
        return False

def _pantry_get(basket_name):
    """Helper function to get data from a Pantry basket."""
    if not PANTRY_ID: return None
    try:
        url = f"{PANTRY_URL}/basket/{basket_name}"
        response = requests.get(url)
        if response.status_code == 404:
            print(f"[INFO] Pantry basket '{basket_name}' not found. This is normal on first run.")
            return {} # Return empty dict for not found
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Could not get from Pantry basket '{basket_name}': {e}")
        return None

def save_conversation(conversation_history):
    """Compresses conversation history and saves it to Pantry."""
    print("Saving conversation to the cloud...")
    history_json = json.dumps(conversation_history)
    compressed_history = zlib.compress(history_json.encode('utf-8')).hex()
    if _pantry_put(CONVERSATION_BASKET, {"history": compressed_history}):
        print(" -> Conversation saved.")

def retrieve_conversation():
    """Retrieves and decompresses conversation history from Pantry."""
    print("Retrieving conversation from the cloud...")
    data = _pantry_get(CONVERSATION_BASKET)
    if data and "history" in data:
        compressed_history_hex = data["history"]
        decompressed_json = zlib.decompress(bytes.fromhex(compressed_history_hex)).decode('utf-8')
        print(" -> Conversation retrieved.")
        return json.loads(decompressed_json)
    return []

def save_metadata(key, value):
    """Saves a key-value pair to the metadata basket in Pantry."""
    current_data = _pantry_get(METADATA_BASKET) or {}
    current_data[key] = value
    _pantry_put(METADATA_BASKET, current_data)

def retrieve_metadata(key):
    """Retrieves a value from the metadata basket by key."""
    data = _pantry_get(METADATA_BASKET)
    return data.get(key) if data else None

def add_learned_fact(topic, data):
    """Adds a new learned fact to the cloud."""
    current_facts = _pantry_get(LEARNED_FACTS_BASKET) or {}
    current_facts[topic.lower()] = data
    _pantry_put(LEARNED_FACTS_BASKET, current_facts)
    add_known_word(topic)

def get_all_learned_facts():
    """Retrieves all learned facts from the cloud."""
    facts = _pantry_get(LEARNED_FACTS_BASKET) or {}
    return "\n".join([f"- {topic.title()}: {data}" for topic, data in facts.items()])

def add_known_word(word):
    """Adds a new word to the set of known words in the cloud."""
    known_words = _pantry_get(KNOWN_WORDS_BASKET) or {"words": []}
    if word.lower() not in known_words["words"]:
        known_words["words"].append(word.lower())
        _pantry_put(KNOWN_WORDS_BASKET, known_words)

def is_word_known(word):
    """Checks if a word is in the set of known words in the cloud."""
    known_words = _pantry_get(KNOWN_WORDS_BASKET) or {"words": []}
    return word.lower() in known_words["words"]

if __name__ == '__main__':
    print("--- Testing memory_manager.py (Pantry Version) ---")
    if not PANTRY_ID:
        print("ERROR: PANTRY_ID not set in .env file. Cannot run test.")
    else:
        save_metadata("test_key", "test_value")
        retrieved_val = retrieve_metadata("test_key")
        print(f"Retrieved metadata: {retrieved_val}")
        assert retrieved_val == "test_value"
        print("--- All Pantry memory tests passed! ---")