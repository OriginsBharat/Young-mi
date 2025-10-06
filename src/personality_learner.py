import os
import ollama
from datetime import datetime

# Import our new memory manager
import src.memory_manager as memory_manager

def digest_all_memories():
    """
    Fetches conversation history and previous summary from Pantry,
    and uses an LLM to generate a new, consolidated summary.
    This new summary OVERWRITES the old one.
    """
    print("--- Starting Personality Digestion ---")

    # Step 1: Retrieve all necessary data from Pantry
    conversation_history = memory_manager.retrieve_conversation()
    old_insights = memory_manager.retrieve_learned_personality()

    if not conversation_history:
        print("No conversation history found to learn from. Skipping.")
        return

    # Convert conversation history to a simple text log
    full_conversation_text = ""
    for message in conversation_history:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        if role == "user":
            full_conversation_text += f"Boyfriend: {content}\n"
        elif role == "assistant":
            full_conversation_text += f"Kim Young-mi: {content}\n"

    print("Data compiled. Asking local AI to generate a new, consolidated summary...")

    # Step 2: Use the LLM to create a new summary from all data
    analysis_prompt = f"""
    You are a relationship analysis AI. Your task is to read the following data and generate a new, consolidated summary of key, permanent facts and memories.
    The data includes a previous summary of learned insights and a log of recent conversations.
    Your new summary should integrate the insights from both sources into a fresh, cohesive, and concise bulleted list. Do NOT simply append the new information.
    Focus on:
    - The boyfriend's personality, likes, dislikes, and habits.
    - Kim Young-mi's personality and how she interacts with him.
    - Shared inside jokes, important past events, and relationship dynamics.

    Data:
    ---
    [Previous Summary of Memories]
    {old_insights}
    ---
    [New Conversation Log]
    {full_conversation_text[-10000:]}
    ---
    """ # Limit to last 10k chars of convo to be safe with context windows

    try:
        model_name = os.getenv("OLLAMA_MODEL", "llama2")
        completion = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a relationship analysis AI. Your output is a new, consolidated, and concise bulleted list of key memories and personality traits, integrating both old and new information."},
                {"role": "user", "content": analysis_prompt}
            ]
        )

        new_consolidated_summary = completion['message']['content']

        print("AI analysis complete. Saving new consolidated summary to the cloud.")

        # Step 3: OVERWRITE the old summary in Pantry with the new one
        memory_manager.save_learned_personality(new_consolidated_summary)

        print("Successfully updated learned personality in the cloud.")

    except Exception as e:
        print(f"An error occurred during personality learning: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("--- Testing Personality Learner (Pantry Version) ---")
    if not os.getenv("PANTRY_ID"):
        print("ERROR: PANTRY_ID not set in .env file. Cannot run test.")
    else:
        digest_all_memories()