import os
from dotenv import load_dotenv
import ollama

import src.memory_manager as memory_manager

# Load environment variables
load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

character_sheet_content = ""

def load_character_sheet():
    """
    Loads the base character sheet, summarized memories, and learned facts
    to create her full, current personality profile.
    """
    global character_sheet_content
    base_personality = ""
    summarized_memories = ""
    learned_facts = ""

    # Load the base character sheet from file
    try:
        with open("data/character_sheet.md", "r", encoding="utf-8") as f:
            base_personality = f.read()
        print("[INFO] Base character sheet loaded successfully.")
    except FileNotFoundError:
        print("[ERROR] data/character_sheet.md not found. Using fallback personality.")
        base_personality = "You are a helpful assistant."

    # Load the summarized long-term memories from the cloud
    summarized_memories = memory_manager.retrieve_metadata("learned_personality")
    if summarized_memories:
        print("[INFO] Summarized memories loaded from the cloud.")

    # Load all individual, autonomously learned facts
    learned_facts = memory_manager.get_all_learned_facts()
    if learned_facts:
        print("[INFO] Autonomously learned facts loaded from the cloud.")

    # Combine everything into the final, comprehensive personality profile
    character_sheet_content = (
        f"{base_personality}\n\n"
        f"--- Consolidated Memories & Personality Insights ---\n{summarized_memories}\n\n"
        f"--- Specific Learned Facts ---\n{learned_facts}"
    )
    print("[INFO] Full personality profile compiled and loaded.")

def get_ai_response(user_input, conversation_history):
    """
    Gets a response from the AI using the local Ollama model.
    """
    if not character_sheet_content:
        # This should only happen once at the very start
        load_character_sheet()

    messages = [{"role": "system", "content": character_sheet_content}]
    # Add a limited number of recent messages to keep context relevant
    messages.extend(conversation_history[-10:])
    messages.append({"role": "user", "content": user_input})

    try:
        print(f"[INFO] Sending request to local model '{OLLAMA_MODEL}'...")
        completion = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages
        )
        response_text = completion['message']['content']
        print("[INFO] Received response from local model.")
        return response_text
    except Exception as e:
        print(f"[ERROR] An error occurred while calling the local Ollama model: {e}")
        print("[ERROR] Please ensure the Ollama application is running and the specified model is downloaded.")
        return "I... I can't think right now. Something's wrong with my connection to myself."

if __name__ == '__main__':
    print("--- Testing thinking.py (Definitive Version) ---")
    memory_manager.initialize_memory()
    load_character_sheet()

    history = []
    print("\nYou can now talk to the AI. Type 'quit' to exit.")
    while True:
        prompt = input("\nYou: ")
        if prompt.lower() == 'quit':
            break

        response = get_ai_response(prompt, history)
        print(f"Kim Young-mi: {response}")

        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": response})