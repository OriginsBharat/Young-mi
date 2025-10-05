import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the OpenAI client with the API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# This will hold the content of the character sheet
character_sheet_content = ""

def load_character_sheet():
    """
    Loads the character sheet from the data directory.
    This is the "soul" of the AI.
    """
    global character_sheet_content
    try:
        with open("data/character_sheet.md", "r", encoding="utf-8") as f:
            character_sheet_content = f.read()
        print("Character sheet loaded successfully.")
    except FileNotFoundError:
        print("Error: data/character_sheet.md not found.")
        character_sheet_content = "You are a helpful assistant." # Fallback personality

def get_ai_response(user_input, conversation_history):
    """
    Gets a response from the AI based on user input and conversation history.
    """
    if not character_sheet_content:
        load_character_sheet()

    # Prepare the messages for the API call
    messages = [
        {"role": "system", "content": character_sheet_content},
    ]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input})

    try:
        print("Sending request to OpenAI...")
        completion = openai.chat.completions.create(
            model="gpt-4o",  # Using a powerful and versatile model
            messages=messages
        )
        response_text = completion.choices[0].message.content
        print("Received response from OpenAI.")
        return response_text
    except Exception as e:
        print(f"An error occurred while calling the OpenAI API: {e}")
        return "I... I can't think right now. Something's wrong."

if __name__ == '__main__':
    # This is for testing the module directly
    load_character_sheet()

    # Simple conversation loop for testing
    history = []
    print("--- Testing thinking.py ---")
    print("You can now talk to the AI. Type 'quit' to exit.")
    while True:
        prompt = input("You: ")
        if prompt.lower() == 'quit':
            break

        response = get_ai_response(prompt, history)
        print(f"Kim Young-mi: {response}")

        # Update history
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": response})