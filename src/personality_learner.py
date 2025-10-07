import os
import ollama
from dotenv import load_dotenv

import src.memory_manager as memory_manager

# Load environment variables
load_dotenv()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def digest_all_memories():
    """
    Fetches conversation history and previous summary from the cloud,
    and uses the local LLM to generate a new, consolidated summary.
    This new summary OVERWRITES the old one to prevent infinite file growth.
    """
    print("[INFO] Starting personality digestion process...")

    # Retrieve all necessary data from the memory manager
    conversation_history = memory_manager.retrieve_conversation()
    old_insights = memory_manager.retrieve_metadata("learned_personality")

    if not conversation_history:
        print("[INFO] No conversation history found to learn from. Skipping.")
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

    print("[INFO] Data compiled. Asking local AI to generate a new, consolidated summary...")

    # Create a detailed prompt for the AI to generate a new summary
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
    {old_insights or "No previous summary."}
    ---
    [New Conversation Log]
    {full_conversation_text[-10000:]}
    ---
    """

    try:
        completion = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a relationship analysis AI. Your output is a new, consolidated, and concise bulleted list of key memories and personality traits, integrating both old and new information."},
                {"role": "user", "content": analysis_prompt}
            ]
        )

        new_consolidated_summary = completion['message']['content']

        print("[INFO] AI analysis complete. Saving new consolidated summary to the cloud.")

        # OVERWRITE the old summary in the cloud with the new one
        memory_manager.save_metadata("learned_personality", new_consolidated_summary)

        print("[INFO] Successfully updated learned personality in the cloud.")

    except Exception as e:
        print(f"[ERROR] An error occurred during personality learning: {e}")

if __name__ == "__main__":
    print("--- Testing personality_learner.py (Definitive Version) ---")
    if not os.getenv("PANTRY_ID"):
        print("[ERROR] PANTRY_ID not set in .env file. Cannot run test.")
    else:
        memory_manager.initialize_memory()
        digest_all_memories()