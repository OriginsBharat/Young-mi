import os
from dotenv import load_dotenv
import ollama

import src.memory_manager as memory_manager
import src.web_search as web_search

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
        print("[INFO] Summarized memories loaded.")

    # Load all individual, autonomously learned facts
    learned_facts = memory_manager.get_all_learned_facts()
    if learned_facts:
        print("[INFO] Autonomously learned facts loaded.")

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

    # First, check if the user is asking about her knowledge base
    if user_input.lower().startswith("what have you learned about"):
        topic = user_input.lower().replace("what have you learned about", "").strip("? .")
        all_facts = memory_manager.get_all_learned_facts()
        # This is a simple string search, could be improved with more advanced NLP
        if topic in all_facts.lower():
             return f"I've learned this about {topic}:\n{all_facts}"
        else:
             # If she doesn't know, she can offer to find out
             return f"I haven't learned anything specific about {topic} yet, but I can look it up for you if you'd like!"

    # Second, check if the query requires a web search
    search_check_prompt = f"Is the following query a request for real-time, external information (like news, specific facts, or how-to guides)? Answer with a single word: YES or NO.\n\nQuery: '{user_input}'"
    search_check = ollama.chat(model=OLLAMA_MODEL, messages=[{'role': 'user', 'content': search_check_prompt}], options={"num_predict": 2})

    if "YES" in search_check['message']['content'].upper():
        search_summary = web_search.search_and_summarize(user_input)
        # Re-frame the input to include the new context for the main personality
        user_input = f"I just looked this up for you and found this: '{search_summary}'. Now, respond to my original question: '{user_input}'"

    # Finally, generate the main response
    messages = [{"role": "system", "content": character_sheet_content}]
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