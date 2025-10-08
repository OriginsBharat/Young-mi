# src/ai_core.py

import ollama
import os
from src.memory import Memory

class AICore:
    def __init__(self, character_sheet_path="data/character_sheet.md"):
        self.client = ollama.Client()
        self.memory = Memory()
        self.system_prompt = self._load_character_sheet(character_sheet_path)

        # Load history from memory or start fresh
        self.conversation_history = self._load_or_initialize_history()

        # Load the model name from environment variables, with a fallback
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3")

    def _load_character_sheet(self, path):
        """Loads the character sheet from a file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Character sheet not found at {path}")
            # Provide a fallback persona if the file is missing
            return "You are a helpful AI assistant."

    def _load_or_initialize_history(self):
        """Loads history from Pantry or creates a new one."""
        retrieved_data = self.memory.get_history()
        if retrieved_data and "messages" in retrieved_data:
            print("Found and loaded previous conversation history.")
            # Ensure the system prompt is always the most current one from the file
            history = retrieved_data["messages"]
            history[0] = {"role": "system", "content": self.system_prompt}
            return history
        else:
            print("No previous history found. Starting a new conversation.")
            return [{"role": "system", "content": self.system_prompt}]

    def generate_response(self, user_input, game_context=None):
        """
        Generates a response, updates history, and saves it to memory.
        """
        # Construct a richer prompt for the AI
        context_prompt = f"Game context: {game_context}\n\nUser says: {user_input}"
        if game_context is None:
            context_prompt = user_input

        self.conversation_history.append({"role": "user", "content": context_prompt})

        # Load the model name from environment variables, with a fallback
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3")

    def __init__(self, character_sheet_path="data/character_sheet.md"):
        self.client = ollama.Client()
        self.memory = Memory()
        self.system_prompt = self._load_character_sheet(character_sheet_path)

        # Load history from memory or start fresh
        self.conversation_history = self._load_or_initialize_history()

        # Load the model name from environment variables, with a fallback
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3")

    def _load_character_sheet(self, path):
        """Loads the character sheet from a file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Character sheet not found at {path}")
            # Provide a fallback persona if the file is missing
            return "You are a helpful AI assistant."

    def _load_or_initialize_history(self):
        """Loads history from Pantry or creates a new one."""
        retrieved_data = self.memory.get_history()
        if retrieved_data and "messages" in retrieved_data:
            print("Found and loaded previous conversation history.")
            # Ensure the system prompt is always the most current one from the file
            history = retrieved_data["messages"]
            history[0] = {"role": "system", "content": self.system_prompt}
            return history
        else:
            print("No previous history found. Starting a new conversation.")
            return [{"role": "system", "content": self.system_prompt}]

    def generate_response(self, user_input, game_context=None):
        """
        Generates a response, updates history, and saves it to memory.
        """
        # Construct a richer prompt for the AI
        context_prompt = f"Game context: {game_context}\n\nUser says: {user_input}"
        if game_context is None:
            context_prompt = user_input

        self.conversation_history.append({"role": "user", "content": context_prompt})

        try:
            response = self.client.chat(
                model=self.model_name,
                messages=self.conversation_history
            )
            ai_response = response['message']['content']
            self.conversation_history.append({"role": "assistant", "content": ai_response})

            # Save the updated history back to our memory store
            self.memory.update_history({"messages": self.conversation_history})

            return ai_response
        except Exception as e:
            print(f"Error communicating with Ollama: {e}")
            return "I'm having a little trouble thinking right now, babe."

if __name__ == '__main__':
    # This block is for testing the module directly
    print("Initializing AI Core for testing...")
    # We need to create a dummy memory module for the test to run
    # since we are not running the full application.
    class DummyMemory:
        def get_history(self): return None
        def update_history(self, data): pass

    # Temporarily patch the memory import for the test
    import src.memory
    src.memory.Memory = DummyMemory

    ai = AICore()
    print("AI Core Initialized. System prompt loaded.")
    print("-" * 20)

    test_input = "Hey, how are you doing?"
    print(f"User: {test_input}")
    # The following line will fail if Ollama is not running, which is expected in this environment.
    # The goal is to confirm the code structure is valid.
    response = ai.generate_response(test_input)
    print(f"Kim Young-mi: {response}")
    print("-" * 20)