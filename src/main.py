import time
import threading
from dotenv import load_dotenv
import collections

# Import our custom modules
import src.thinking as thinking
import src.speaking as speaking
import src.listening as listening
import src.game_awareness as game_awareness

# Load environment variables from .env file
load_dotenv()

# --- Global State & Configuration ---
app_running = True
conversation_history = []
# Use a deque to keep track of recent events to avoid spamming reactions
recent_events = collections.deque(maxlen=5)
EVENT_COOLDOWN = 10 # Seconds to wait before reacting to the same type of event

def trigger_ai_reaction(event_type, event_details=""):
    """
    Triggers the AI to react to a game event.
    This function gets the AI's thought, speaks it, and updates history.
    """
    global conversation_history

    # 1. Check if this event is too recent
    current_time = time.time()
    for event, timestamp in recent_events:
        if event == event_type and (current_time - timestamp) < EVENT_COOLDOWN:
            # print(f"Skipping event '{event_type}' due to cooldown.")
            return

    # If not on cooldown, add it to recent events
    recent_events.append((event_type, current_time))

    # 2. Create a system prompt based on the event
    system_prompt = f"[Game Event: {event_type}. {event_details}]"
    print(f"--- New Game Event Detected: {system_prompt} ---")

    # 3. Get the AI's reaction from the thinking module
    ai_response = thinking.get_ai_response(system_prompt, conversation_history)

    # 4. Speak the response
    speaking.speak(ai_response)

    # 5. Update the conversation history
    conversation_history.append({"role": "system", "content": system_prompt})
    conversation_history.append({"role": "assistant", "content": ai_response})

def game_event_monitor():
    """
    A background thread that constantly checks for game events and triggers reactions.
    """
    print("Game Event Monitor started.")
    welcomed_to_lobby = False

    while app_running:
        # Check for lobby first
        if not welcomed_to_lobby and game_awareness.is_valorant_lobby_open():
            welcomed_to_lobby = True
            trigger_ai_reaction("PLAYER_ENTERED_LOBBY", "You've just booted up the game. Greet your boyfriend.")
            # Give a longer cooldown after the welcome message
            time.sleep(20)
            continue

        # Check for in-game events
        if game_awareness.check_for_kill():
            trigger_ai_reaction("PLAYER_KILL")

        if game_awareness.check_for_death():
            trigger_ai_reaction("PLAYER_DEATH")

        round_status = game_awareness.check_round_end()
        if round_status == "VICTORY":
            trigger_ai_reaction("ROUND_WON")
        elif round_status == "DEFEAT":
            trigger_ai_reaction("ROUND_LOST")

        # Check for these events every 2 seconds to be responsive but not wasteful
        time.sleep(2)

def user_conversation_handler():
    """
    A background thread that handles proactive conversation from the user.
    """
    print("User Conversation Handler started.")
    while app_running:
        # Listen for the user to speak
        user_input = listening.listen_for_command()

        if user_input:
            # Get AI response and speak it
            ai_response = thinking.get_ai_response(user_input, conversation_history)
            speaking.speak(ai_response)

            # Update history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": ai_response})

        time.sleep(0.1)


def main():
    """
    Main function to initialize and run the Kim Young-mi AI.
    """
    global app_running

    print("Starting Kim Young-mi AI (Advanced V1)...")

    # --- Initialization ---
    thinking.load_character_sheet()
    speaking.initialize_tts()

    print("\n--- Instructions ---")
    print(f"1. IMPORTANT: Make sure your in-game name is set in 'src/game_awareness.py'. Currently: '{game_awareness.PLAYER_USERNAME}'")
    print("2. Make sure you have created a '.env' file with your OPENAI_API_KEY.")
    print("3. Make sure you have created 'data/templates/valorant_lobby_template.png'.")
    print("4. The AI is now running. She will greet you when you enter the Valorant lobby.")
    print("5. She will react to game events and you can also speak to her at any time.")
    print("Press Ctrl+C in this terminal to stop the application.")
    print("--------------------\n")

    # --- Start Background Threads ---
    event_thread = threading.Thread(target=game_event_monitor, daemon=True)
    conv_thread = threading.Thread(target=user_conversation_handler, daemon=True)

    event_thread.start()
    conv_thread.start()

    try:
        # Keep the main thread alive to handle shutdown
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Kim Young-mi AI...")
        app_running = False
        # Wait for threads to finish
        event_thread.join()
        conv_thread.join()
        print("Goodbye.")

if __name__ == "__main__":
    main()