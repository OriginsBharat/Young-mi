# src/memory.py

import requests
import os
from dotenv import load_dotenv

class Memory:
    def __init__(self, basket_name="kim_young_mi_history"):
        load_dotenv()
        self.pantry_id = os.getenv("PANTRY_ID")
        self.basket_name = basket_name
        self.base_url = f"https://getpantry.cloud/apiv1/pantry/{self.pantry_id}"
        self.headers = {"Content-Type": "application/json"}

        if not self.pantry_id:
            print("[Warning] PANTRY_ID not found in .env file. Memory will not be persistent.")

    def get_history(self):
        """Retrieves conversation history from the Pantry.io API."""
        if not self.pantry_id:
            return None

        url = f"{self.base_url}/basket/{self.basket_name}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError:
                    print(f"No history found in basket '{self.basket_name}'. A new one will be created on the next interaction.")
                    return None
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving history from Pantry: {e}")
            return None

    def update_history(self, conversation_data):
        """Updates conversation history in the Pantry.io API."""
        if not self.pantry_id:
            return

        url = f"{self.base_url}/basket/{self.basket_name}"
        try:
            response = requests.post(url, json=conversation_data, headers=self.headers)
            response.raise_for_status()
            print("Memory successfully updated.")
        except requests.exceptions.RequestException as e:
            print(f"Error updating Pantry history: {e}")