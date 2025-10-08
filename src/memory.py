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
                # Pantry returns a 200 with a message for empty/non-existent baskets,
                # so we check if the response is actually JSON.
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
            # Pantry will create the basket if it doesn't exist, or overwrite it if it does.
            response = requests.post(url, json=conversation_data, headers=self.headers)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            print("Memory successfully updated.")
        except requests.exceptions.RequestException as e:
            print(f"Error updating Pantry history: {e}")

if __name__ == '__main__':
    # This block is for testing the module directly
    print("Testing Memory module with direct API calls...")

    if not os.path.exists('.env'):
        print("Creating a dummy .env file for testing.")
        with open('.env', 'w') as f:
            f.write('PANTRY_ID=YOUR_PANTRY_ID_HERE\n')

    memory = Memory(basket_name="memory_test_basket")

    if memory.pantry_id and "YOUR_PANTRY_ID" not in memory.pantry_id:
        print(f"Pantry client configured for Pantry ID: {memory.pantry_id}")

        dummy_history = {"messages": [{"role": "system", "content": "Test"}]}

        print("\n1. Attempting to update history...")
        memory.update_history(dummy_history)

        print("\n2. Attempting to retrieve history...")
        retrieved = memory.get_history()

        if retrieved:
            print("\n   Successfully retrieved history:")
            print(f"   {retrieved}")
        else:
            print("\n   Failed to retrieve history.")

        print("\n3. Cleaning up test basket...")
        try:
            delete_url = f"{memory.base_url}/basket/memory_test_basket"
            requests.delete(delete_url)
            print("   Test basket deleted.")
        except requests.exceptions.RequestException as e:
            print(f"   Could not delete test basket: {e}")
    else:
        print("\nCould not perform live test.")
        print("Please create a real .env file with your Pantry ID and run this test again.")
        print("Example: PANTRY_ID=a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890")