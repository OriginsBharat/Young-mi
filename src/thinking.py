import openai
import os
from dotenv import load_dotenv
import src.web_search as web_search # Import the new module

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

character_sheet_content = ""

def load_character_sheet():
    """
    Loads the base character sheet and any learned personality traits,
    combining them into a single personality profile.
    """
    global character_sheet_content
    base_personality = ""
    learned_personality = ""

    # Load the base character sheet
    try:
        with open("data/character_sheet.md", "r", encoding="utf-8") as f:
            base_personality = f.read()
        print("Base character sheet loaded successfully.")
    except FileNotFoundError:
        print("Error: data/character_sheet.md not found. Using fallback personality.")
        base_personality = "You are a helpful assistant."

    # Load the learned personality traits if they exist
    learned_personality_file = "data/learned_personality.md"
    if os.path.exists(learned_personality_file):
        try:
            with open(learned_personality_file, "r", encoding="utf-8") as f:
                learned_personality = f.read()
            print("Learned personality traits loaded successfully.")
        except Exception as e:
            print(f"Error loading learned personality file: {e}")

    # Combine them into the final character sheet
    character_sheet_content = f"{base_personality}\n\n--- Additional Memories and Learned Insights ---\n{learned_personality}"

def needs_web_search(user_input):
    """
    Uses the LLM to quickly determine if a user's query requires a web search.
    """
    try:
        # This is a very simple, fast check.
        completion = openai.chat.completions.create(
            model="gpt-4o",
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
            max_tokens=5,
            temperature=0
        )
        decision = completion.choices[0].message.content.strip().upper()
        print(f"Search decision for '{user_input}': {decision}")
        return decision == "SEARCH"
    except Exception as e:
        print(f"Error in needs_web_search check: {e}")
        return False


def get_ai_response(user_input, conversation_history):
    """
    Gets a response from the AI, first deciding if it needs to search the web.
    """
    if not character_sheet_content:
        load_character_sheet()

    # Check if the query requires a web search
    if needs_web_search(user_input):
        search_summary = web_search.search_and_summarize(user_input)
        # We'll add the search result as special context for the main AI
        user_input_with_context = f"I just looked this up for you and found this information: '{search_summary}'. Now, answer my original question: '{user_input}'"
    else:
        user_input_with_context = user_input

    # Prepare the messages for the main API call
    messages = [{"role": "system", "content": character_sheet_content}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input_with_context})

    try:
        print("Sending request to OpenAI for final response...")
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        response_text = completion.choices[0].message.content
        print("Received final response from OpenAI.")
        return response_text
    except Exception as e:
        print(f"An error occurred while calling the OpenAI API: {e}")
        return "I... I can't think right now. Something's wrong."

if __name__ == '__main__':
    print("--- Testing thinking.py (with Web Intelligence) ---")
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