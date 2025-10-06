import os
import zlib
import json
import openai
from datetime import datetime
from google.cloud import firestore

# Import our existing memory manager to reuse the firestore connection
import src.memory_manager as memory_manager

LEARNED_PERSONALITY_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'learned_personality.md')

def digest_all_memories(user_id):
    """
    Fetches all conversation history and previous summaries, and uses an LLM
    to generate a new, consolidated summary of the user's personality and relationship.
    This new summary OVERWRITES the old one to prevent infinite file growth.
    """
    if not memory_manager.db:
        print("Cloud memory not initialized. Cannot run personality learning.")
        return

    print("Fetching all conversation history and previous memories...")
    try:
        # Step 1: Get all conversation documents from Firestore
        docs = memory_manager.db.collection(f'users/{user_id}/conversations').stream()

        full_conversation_text = ""
        for doc in docs:
            compressed_history = doc.to_dict().get('compressed_history')
            if not compressed_history: continue

            decompressed_json = zlib.decompress(compressed_history).decode('utf-8')
            conversation_history = json.loads(decompressed_json)

            for message in conversation_history:
                role = message.get("role", "unknown")
                content = message.get("content", "")
                if role == "user":
                    full_conversation_text += f"Boyfriend: {content}\n"
                elif role == "assistant":
                    full_conversation_text += f"Kim Young-mi: {content}\n"

        if not full_conversation_text:
            print("No conversation history found to learn from.")
            return

        # Step 2: Get the previously learned insights
        old_insights = ""
        if os.path.exists(LEARNED_PERSONALITY_FILE):
            with open(LEARNED_PERSONALITY_FILE, "r", encoding="utf-8") as f:
                old_insights = f.read()

        print("Data compiled. Asking AI to generate a new, consolidated summary...")

        # Step 3: Use the LLM to create a new summary from all data
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
        {full_conversation_text[:10000]}
        ---
        """ # Limit content to be safe with token limits

        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a relationship analysis AI. Your output is a new, consolidated, and concise bulleted list of key memories and personality traits, integrating both old and new information."},
                {"role": "user", "content": analysis_prompt}
            ]
        )

        new_consolidated_summary = completion.choices[0].message.content

        print("AI analysis complete. Saving new consolidated summary.")

        # Step 4: OVERWRITE the old file with the new summary
        with open(LEARNED_PERSONALITY_FILE, "w", encoding="utf-8") as f:
            f.write(f"--- Memories Consolidated on {datetime.now().strftime('%Y-%m-%d')} ---\n")
            f.write(new_consolidated_summary)

        print(f"Successfully updated learned personality file at: {LEARNED_PERSONALITY_FILE}")

    except Exception as e:
        print(f"An error occurred during personality learning: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    print("--- Testing Personality Learner (Consolidated Summary Version) ---")
    if memory_manager.initialize_memory():
        test_user = "test_user_123"
        digest_all_memories(test_user)
    else:
        print("Could not run test because cloud memory failed to initialize.")