import os
from dotenv import load_dotenv
import ollama

import src.web_search as web_search
import src.memory_manager as memory_manager # V6 Memory

# Load environment variables
load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

character_sheet_content = ""

def load_character_sheet():
    """
    Loads the base character sheet and any learned personality traits from the cloud,
    combining them into a single personality profile.
    """
    global character_sheet_content
    base_personality = ""
    learned_personality = ""

    try:
        with open("data/character_sheet.md", "r", encoding="utf-8") as f:
            base_personality = f.read()
        print("Base character sheet loaded successfully.")
    except FileNotFoundError:
        print("Error: data/character_sheet.md not found. Using fallback personality.")
        base_personality = "You are a helpful assistant."

    # V6: Load learned personality from the cloud via memory_manager
    learned_personality = memory_manager.retrieve_learned_personality()
    if learned_personality:
        print("Learned personality traits loaded from the cloud.")

    character_sheet_content = f"{base_personality}\n\n--- Additional Memories and Learned Insights ---\n{learned_personality}"

def needs_web_search(user_input):
    """
    Uses the local LLM to quickly determine if a user's query requires a web search.
    """
    try:
        completion = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a classification model. Your only job is to determine if a user's query requires a real-time web search to answer. Respond with a single word: 'SEARCH' if it does, and 'CONVERSE' if it does not. Queries about current events, specific facts, or 'how-to' guides need a search. Personal questions or conversational remarks do not."},
                {"role": "user", "content": f"Query: 'Who won the last VCT championship?'"},
                {"role": "assistant", "content": "SEARCH"},
                {"role": "user", "content": f"Query: 'What do you think of my new haircut?'"},
                {"role": "assistant", "content": "CONVERSE"},
                {"role": "user", "content": f"Query: 'How do you play Viper on the map Bind?'"},
                {"role": "assistant", "content": "SEARCH"},
                {"role": "user", "content": f"Query: '{user_input}'"}
            ],
            options={"num_predict": 5}
        )
        decision = completion['message']['content'].strip().upper()
        print(f"Search decision for '{user_input}': {decision}")
        return "SEARCH" in decision
    except Exception as e:
        print(f"Error in needs_web_search check: {e}")
        return False

def get_ai_response(user_input, conversation_history):
    """
    Gets a response from the AI, first deciding if it needs to search the web.
    """
    if not character_sheet_content:
        load_character_sheet()

    if needs_web_search(user_input):
        search_summary = web_search.search_and_summarize(user_input)
        user_input_with_context = f"I just looked this up for you and found this information: '{search_summary}'. Now, answer my original question: '{user_input}'"
    else:
        user_input_with_context = user_input

    messages = [{"role": "system", "content": character_sheet_content}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input_with_context})

    try:
        print(f"Sending request to local model '{OLLAMA_MODEL}'...")
        completion = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages
        )
        response_text = completion['message']['content']
        print("Received response from local model.")
        return response_text
    except Exception as e:
        print(f"An error occurred while calling the local Ollama model: {e}")
        print("Please ensure the Ollama application is running and the specified model is downloaded.")
        return "I... I can't think right now. Something's wrong with my connection to myself."

if __name__ == '__main__':
    print("--- Testing thinking.py (with Local Ollama & Pantry Memory) ---")
    load_character_sheet()
    history = []
    print("You can now talk to the AI. Type 'quit' to exit.")
    while True:
        prompt = input("You: ")
        if prompt.lower() == 'quit':
            break

        response = get_ai_response(prompt, history)
        print(f"Kim Young-mi: {response}")

        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": response})