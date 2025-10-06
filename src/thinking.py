import os
from dotenv import load_dotenv
import ollama

import src.web_search as web_search
import src.memory_manager as memory_manager

# Load environment variables
load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

character_sheet_content = ""

def load_character_sheet():
    """
    V9: Loads the base character sheet, the summarized long-term memories, AND
    all individually learned facts to create her full, current personality.
    """
    global character_sheet_content
    base_personality = ""
    summarized_memories = ""
    learned_facts = ""

    # Load the base character sheet from file
    try:
        with open("data/character_sheet.md", "r", encoding="utf-8") as f:
            base_personality = f.read()
        print("Base character sheet loaded successfully.")
    except FileNotFoundError:
        print("Error: data/character_sheet.md not found. Using fallback personality.")
        base_personality = "You are a helpful assistant."

    # Load the summarized memories from her long-term storage
    summarized_memories = memory_manager.retrieve_learned_personality()
    if summarized_memories:
        print("Summarized memories loaded from the cloud.")

    # V9: Load all individual, autonomously learned facts
    learned_facts = memory_manager.get_all_learned_facts()
    if learned_facts:
        print("Autonomously learned facts loaded from local memory.")

    # Combine everything into the final, comprehensive personality profile
    character_sheet_content = (
        f"{base_personality}\n\n"
        f"--- Consolidated Memories & Personality Insights ---\n{summarized_memories}\n\n"
        f"--- Specific Learned Facts ---\n{learned_facts}"
    )
    print("Full personality profile compiled and loaded.")

def needs_web_search(user_input):
    """
    Uses the local LLM to quickly determine if a user's query requires a web search.
    """
    try:
        completion = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a classification model. Your only job is to determine if a user's query requires a real-time web search to answer. Respond with a single word: 'SEARCH' if it does, and 'CONVERSE' if it does not. Queries about current events, specific facts, or 'how-to' guides need a search. Personal questions or conversational remarks do not."},
                {"role": "user", "content": f"Query: '{user_input}'"}
            ],
            options={"num_predict": 5}
        )
        decision = completion['message']['content'].strip().upper()
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

    if "what have you learned about" in user_input.lower():
        # A special command to check her knowledge
        topic = user_input.lower().replace("what have you learned about", "").strip()
        all_facts = memory_manager.get_all_learned_facts()
        if topic in all_facts.lower():
             return f"I've learned this about {topic}:\n{all_facts}"
        else:
             return f"I haven't learned anything specific about {topic} yet, but I can look it up!"

    if needs_web_search(user_input):
        search_summary = web_search.search_and_summarize(user_input)
        user_input_with_context = f"I just looked this up for you and found this information: '{search_summary}'. Now, answer my original question: '{user_input}'"
    else:
        user_input_with_context = user_input

    messages = [{"role": "system", "content": character_sheet_content}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input_with_context})

    try:
        completion = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages
        )
        response_text = completion['message']['content']
        return response_text
    except Exception as e:
        print(f"An error occurred while calling the local Ollama model: {e}")
        return "I... I can't think right now. Something's wrong with my connection to myself."

if __name__ == '__main__':
    print("--- Testing thinking.py (V9 Meaningful Learning) ---")
    memory_manager.initialize_memory() # Need to init memory for testing
    load_character_sheet()
    print("\nFinal Compiled Character Sheet:")
    print(character_sheet_content)

    history = []
    print("\nYou can now talk to the AI. Try asking 'what have you learned about Clove'. Type 'quit' to exit.")
    while True:
        prompt = input("\nYou: ")
        if prompt.lower() == 'quit':
            break

        response = get_ai_response(prompt, history)
        print(f"Kim Young-mi: {response}")

        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": response})