import os
import requests
import zlib
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- V6: Pantry Configuration ---
PANTRY_ID = os.getenv("PANTRY_ID")
PANTRY_URL = f"https://getpantry.cloud/apiv1/pantry/{PANTRY_ID}"

# We will use different "baskets" (endpoints) for different data types
CONVERSATION_BASKET = "conversation_history"
METADATA_BASKET = "metadata"
LEARNED_BASKET = "learned_personality"

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
        print(f"Error saving to Pantry basket '{basket_name}': {e}")
        return False

def _pantry_get(basket_name):
    """Helper function to get data from a Pantry basket."""
    if not PANTRY_ID: return None
    try:
        url = f"{PANTRY_URL}/basket/{basket_name}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Pantry basket '{basket_name}' not found. This is normal on first run.")
        else:
            print(f"Error getting from Pantry basket '{basket_name}': {e}")
        return None
    except Exception as e:
        print(f"Error getting from Pantry basket '{basket_name}': {e}")
        return None

def save_conversation(conversation_history):
    """Compresses conversation history and saves it to Pantry."""
    print("Saving conversation to the cloud...")
    history_json = json.dumps(conversation_history)
    compressed_history = zlib.compress(history_json.encode('utf-8')).hex() # hex for JSON compatibility
    if _pantry_put(CONVERSATION_BASKET, {"history": compressed_history}):
        print("Successfully saved compressed conversation.")

def retrieve_conversation():
    """Retrieves and decompresses conversation history from Pantry."""
    print("Retrieving conversation from the cloud...")
    data = _pantry_get(CONVERSATION_BASKET)
    if data and "history" in data:
        compressed_history_hex = data["history"]
        decompressed_json = zlib.decompress(bytes.fromhex(compressed_history_hex)).decode('utf-8')
        print("Successfully retrieved and decompressed conversation.")
        return json.loads(decompressed_json)
    return []

def save_last_seen_timestamp():
    """Saves the current timestamp to Pantry."""
    print("Saving last_seen timestamp to the cloud...")
    timestamp = {"last_seen": int(time.time())}
    if _pantry_put(METADATA_BASKET, timestamp):
        print("Successfully saved timestamp.")

def retrieve_last_seen_timestamp():
    """Retrieves the last_seen timestamp from Pantry."""
    print("Retrieving last_seen timestamp from the cloud...")
    data = _pantry_get(METADATA_BASKET)
    if data and "last_seen" in data:
        print("Successfully retrieved timestamp.")
        return data["last_seen"]
    return None

def save_learned_personality(insights):
    """Saves the learned personality insights to Pantry."""
    print("Saving learned personality to the cloud...")
    if _pantry_put(LEARNED_BASKET, {"insights": insights}):
        print("Successfully saved learned personality.")

def retrieve_learned_personality():
    """Retrieves the learned personality insights from Pantry."""
    print("Retrieving learned personality from the cloud...")
    data = _pantry_get(LEARNED_BASKET)
    if data and "insights" in data:
        print("Successfully retrieved learned personality.")
        return data["insights"]
    return ""

if __name__ == '__main__':
    import time
    print("--- Testing memory_manager.py (Pantry Version) ---")
    if not PANTRY_ID:
        print("ERROR: PANTRY_ID not set in .env file. Cannot run test.")
    else:
        # Test conversation
        test_history = [{"role": "user", "content": f"Test message at {time.time()}"}]
        save_conversation(test_history)
        retrieved = retrieve_conversation()
        print(f"Retrieved: {retrieved}")
        assert test_history == retrieved

        # Test timestamp
        save_last_seen_timestamp()
        retrieved_ts = retrieve_last_seen_timestamp()
        print(f"Retrieved timestamp: {retrieved_ts}")
        assert isinstance(retrieved_ts, int)

        # Test personality
        test_insights = "Learned that the user likes testing things."
        save_learned_personality(test_insights)
        retrieved_insights = retrieve_learned_personality()
        print(f"Retrieved insights: {retrieved_insights}")
        assert test_insights == retrieved_insights

        print("\n--- All Pantry tests passed! ---")