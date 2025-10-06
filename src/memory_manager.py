import firebase_admin
from firebase_admin import credentials, firestore
import zlib
import json
import os
from datetime import datetime

# This module will handle the connection to Firestore and data compression.

db = None

def initialize_memory():
    """
    Initializes the connection to the Firestore database.
    It uses the service account key specified in the environment variable.
    """
    global db
    try:
        # The GOOGLE_APPLICATION_CREDENTIALS env var is automatically used by the library.
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            print("WARNING: GOOGLE_APPLICATION_CREDENTIALS not set. Cloud memory will be disabled.")
            return False

        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {
            'projectId': os.getenv('GCLOUD_PROJECT'), # Assumes project ID is also set
        })
        db = firestore.client()
        print("Cloud memory initialized successfully.")
        return True
    except Exception as e:
        print(f"Failed to initialize Firestore: {e}")
        print("Please ensure your GOOGLE_APPLICATION_CREDENTIALS path is correct and you have authenticated.")
        return False

def compress_and_save_conversation(user_id, conversation_history):
    """
    Compresses the conversation history and saves it to Firestore.
    """
    if not db:
        print("Cloud memory not available. Cannot save conversation.")
        return

    try:
        # Convert the conversation history (a list of dicts) to a JSON string
        history_json = json.dumps(conversation_history)
        # Compress the JSON string using zlib
        compressed_history = zlib.compress(history_json.encode('utf-8'))

        # Create a document in Firestore. We'll use the current timestamp for the document ID.
        doc_ref = db.collection(f'users/{user_id}/conversations').document(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        doc_ref.set({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'compressed_history': compressed_history
        })
        print(f"Successfully saved compressed conversation to the cloud.")

    except Exception as e:
        print(f"Error saving conversation to cloud: {e}")


def retrieve_and_decompress_last_conversation(user_id):
    """
    Retrieves the most recent conversation from Firestore and decompresses it.
    """
    if not db:
        print("Cloud memory not available. Cannot retrieve conversation.")
        return []

    try:
        # Query the collection to get the most recent conversation document
        docs = db.collection(f'users/{user_id}/conversations').order_by(
            'timestamp', direction=firestore.Query.DESCENDING).limit(1).stream()

        doc = next(docs, None)
        if doc:
            compressed_history = doc.to_dict()['compressed_history']
            # Decompress the data
            decompressed_json = zlib.decompress(compressed_history).decode('utf-8')
            # Convert the JSON string back to a Python list
            conversation_history = json.loads(decompressed_json)
            print("Successfully retrieved and decompressed the last conversation from the cloud.")
            return conversation_history
        else:
            print("No previous conversations found in the cloud.")
            return []

    except Exception as e:
        print(f"Error retrieving conversation from cloud: {e}")
        return []

def save_last_seen_timestamp(user_id):
    """Saves the current timestamp to the user's profile in Firestore."""
    if not db: return
    try:
        doc_ref = db.collection(f'users/{user_id}/profile').document('metadata')
        doc_ref.set({'last_seen': firestore.SERVER_TIMESTAMP}, merge=True)
        print("Saved last_seen timestamp to the cloud.")
    except Exception as e:
        print(f"Error saving last_seen timestamp: {e}")

def retrieve_last_seen_timestamp(user_id):
    """Retrieves the last_seen timestamp from the user's profile."""
    if not db: return None
    try:
        doc_ref = db.collection(f'users/{user_id}/profile').document('metadata')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get('last_seen')
        return None
    except Exception as e:
        print(f"Error retrieving last_seen timestamp: {e}")
        return None

if __name__ == '__main__':
    # This is for testing the module directly
    print("--- Testing memory_manager.py ---")
    # You need to have your GCLOUD_PROJECT env var set for this to work.
    # And you need to be authenticated with `gcloud auth application-default login`
    if initialize_memory():
        test_user = "test_user_123"
        test_history = [
            {"role": "user", "content": "Hello, this is a test."},
            {"role": "assistant", "content": "I am testing the memory system."}
        ]

        print("\n1. Saving a test conversation...")
        compress_and_save_conversation(test_user, test_history)

        print("\n2. Retrieving the last conversation...")
        retrieved_history = retrieve_and_decompress_last_conversation(test_user)

        print("\nRetrieved History:")
        print(retrieved_history)

        assert test_history == retrieved_history
        print("\nTest successful: Saved and retrieved history matches.")
    else:
        print("\nCould not run test because cloud memory failed to initialize.")