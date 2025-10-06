import time
import threading
from dotenv import load_dotenv
import collections

# Import our custom modules
import src.thinking as thinking
import src.speaking as speaking
import src.listening as listening
import src.game_awareness as game_awareness

# Load environment variables
load_dotenv()

# --- Global State & Configuration ---
app_running = True
conversation_history = []
current_game_state = "UNKNOWN"
last_game_state = "UNKNOWN"

# Use a deque to manage event cooldowns and prevent spam
recent_events = collections.deque(maxlen=10)
EVENT_COOLDOWN = 15  # Seconds to wait before reacting to the same type of event

def trigger_ai_reaction(event_type, event_details=""):
    """Triggers the AI to react to a game event, checking for cooldowns."""
    global conversation_history

    current_time = time.time()
    # Check if this exact event happened recently
    for event, timestamp in recent_events:
        if event == event_type and (current_time - timestamp) < EVENT_COOLDOWN:
            # print(f"Skipping event '{event_type}' due to cooldown.")
            return

    recent_events.append((event_type, current_time))

    system_prompt = f"[Game Event: {event_type}. {event_details}]"
    print(f"--- New Game Event Detected: {system_prompt} ---")

    ai_response = thinking.get_ai_response(system_prompt, conversation_history)
    speaking.speak(ai_response)

    conversation_history.append({"role": "system", "content": system_prompt})
    conversation_history.append({"role": "assistant", "content": ai_response})

def game_state_manager():
    """
    The core logic loop. Manages the AI's state based on the game screen
    and triggers context-appropriate event checks.
    """
    global app_running, current_game_state, last_game_state
    print("Game State Manager started.")

    while app_running:
        # Determine the current screen
        current_game_state = game_awareness.get_current_screen()

        # --- State Change Logic ---
        if current_game_state != last_game_state:
            print(f"STATE CHANGE: Moving from '{last_game_state}' to '{current_game_state}'")
            # Trigger a reaction based on the new screen
            trigger_ai_reaction(f"SCREEN_CHANGED_TO_{current_game_state}", f"You are now on the {current_game_state} screen.")
            last_game_state = current_game_state

        # --- State-Specific Logic ---
        if current_game_state == "IN_MATCH":
            # Only check for match-related events when in a match
            if game_awareness.check_for_kill():
                trigger_ai_reaction("PLAYER_KILL")

            if game_awareness.check_for_death():
                trigger_ai_reaction("PLAYER_DEATH")

            round_status = game_awareness.check_round_end()
            if round_status == "VICTORY":
                trigger_ai_reaction("ROUND_WON")
            elif round_status == "DEFEAT":
                trigger_ai_reaction("ROUND_LOST")

        # Adjust sleep time based on state to be more efficient
        sleep_time = 2 if current_game_state == "IN_MATCH" else 5
        time.sleep(sleep_time)

def user_conversation_handler():
    """A background thread that handles proactive conversation from the user."""
    print("User Conversation Handler started.")
    while app_running:
        user_input = listening.listen_for_command()
        if user_input:
            ai_response = thinking.get_ai_response(user_input, conversation_history)
            speaking.speak(ai_response)
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": ai_response})
        time.sleep(0.1)

def main():
    global app_running
    print("Starting Kim Young-mi AI (V2 - Attentive Companion)...")

    # Initialization
    thinking.load_character_sheet()
    speaking.initialize_tts()

    print("\n--- Instructions ---")
    print(f"1. IMPORTANT: Make sure your in-game name is set in 'src/game_awareness.py'. Currently: '{game_awareness.PLAYER_USERNAME}'")
    print("2. Make sure you have a .env file with your OPENAI_API_KEY.")
    print("3. The AI is now running. She will react to you changing screens and to in-game events.")
    print("Press Ctrl+C in this terminal to stop the application.")
    print("--------------------\n")

    # Start background threads
    state_thread = threading.Thread(target=game_state_manager, daemon=True)
    conv_thread = threading.Thread(target=user_conversation_handler, daemon=True)

    state_thread.start()
    conv_thread.start()

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Kim Young-mi AI...")
        app_running = False
        state_thread.join()
        conv_thread.join()
        print("Goodbye.")

if __name__ == "__main__":
    main()