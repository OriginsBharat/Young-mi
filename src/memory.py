# src/memory.py
# This module handles the AI's long-term memory using the JSONBin.io API.

import requests
import os
from dotenv import load_dotenv, set_key

class Memory:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("JSONBIN_API_KEY")
        self.bin_name = os.getenv("JSONBIN_BIN_NAME", "kim_young_mi_history")
        # The Bin ID is the crucial piece. We'll try to load it from the .env file.
        # If it's not there, we'll create a new bin on the first memory update.
        self.bin_id = os.getenv("JSONBIN_BIN_ID")

        self.base_url = "https://api.jsonbin.io/v3/b"
        self.headers = {
            'Content-Type': 'application/json',
            'X-Master-Key': self.api_key
        }

        if not self.api_key:
            print("[Warning] JSONBIN_API_KEY not found in .env file. Memory will not be persistent.")

    def _create_new_bin(self, initial_data):
        """Creates a new bin on JSONBin.io and saves its ID."""
        if not self.api_key:
            return None

        print(f"[Memory] No Bin ID found. Creating a new bin named '{self.bin_name}' on JSONBin.io...")
        create_headers = self.headers.copy()
        create_headers['X-Bin-Name'] = self.bin_name
        # Make the bin private so only you can access it
        create_headers['X-Bin-Private'] = 'true'

        try:
            response = requests.post(self.base_url, json=initial_data, headers=create_headers)
            response.raise_for_status()
            result = response.json()

            new_bin_id = result.get("metadata", {}).get("id")
            if not new_bin_id:
                print("[ERROR] Failed to get new Bin ID from JSONBin.io response.")
                return None

            print(f"  > New bin created successfully! Bin ID: {new_bin_id}")
            self.bin_id = new_bin_id

            # Save the new Bin ID to the .env file for future use
            dotenv_path = '.env'
            set_key(dotenv_path, "JSONBIN_BIN_ID", self.bin_id)
            print(f"  > Bin ID saved to .env file for future sessions.")

            return new_bin_id
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to create new bin on JSONBin.io: {e}")
            return None

    def get_history(self):
        """Retrieves conversation history from the JSONBin.io API."""
        if not self.api_key or not self.bin_id:
            return None

        url = f"{self.base_url}/{self.bin_id}/latest"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 404:
                print(f"Bin with ID '{self.bin_id}' not found. A new one will be created.")
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving history from JSONBin.io: {e}")
            return None

    def update_history(self, conversation_data):
        """Updates conversation history in the JSONBin.io API."""
        if not self.api_key:
            return

        # If we don't have a Bin ID, this is the first time we're saving memory.
        # We need to create a new bin first.
        if not self.bin_id:
            self._create_new_bin(conversation_data)
            return # The creation call already uploaded the data.

        # If we already have a Bin ID, we just update the existing bin.
        url = f"{self.base_url}/{self.bin_id}"
        try:
            response = requests.put(url, json=conversation_data, headers=self.headers)
            response.raise_for_status()
            print("Memory successfully updated.")
        except requests.exceptions.RequestException as e:
            print(f"Error updating JSONBin.io history: {e}")