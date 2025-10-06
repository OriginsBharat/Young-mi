import time
import threading
from dotenv import load_dotenv
import collections
import queue

# Import our custom modules
import src.thinking as thinking
import src.speaking as speaking
import src.listening as listening
import src.game_awareness as game_awareness
import src.game_data as game_data
import src.chat_gui as chat_gui

# Load environment variables
load_dotenv()

# --- Global State & Configuration ---
app_running = True
conversation_history = []
current_game_state = "UNKNOWN"
last_game_state = "UNKNOWN"
last_user_interaction_time = 0

# Communication queues for the GUI
gui_input_queue = queue.Queue()
gui_output_queue = queue.Queue()

# Cooldowns to prevent spam
EVENT_COOLDOWN = 15
CONVERSATION_TIMEOUT = 45
recent_events = collections.deque(maxlen=10)

def trigger_ai_reaction(event_type, event_details="", is_game_event=False):
    """Triggers the AI to react to an event, now with a check for active conversation."""
    global conversation_history

    current_time = time.time()
    if is_game_event and (current_time - last_user_interaction_time) < CONVERSATION_TIMEOUT:
        print(f"Skipping game event '{event_type}' because of active conversation.")
        return

    for event, timestamp in recent_events:
        if event == event_type and (current_time - timestamp) < EVENT_COOLDOWN:
            return

    recent_events.append((event_type, current_time))

    system_prompt = f"[Game Event: {event_type}. {event_details}]"
    print(f"--- New Game Event Detected: {system_prompt} ---")
    gui_output_queue.put((f"[{event_type}]", 'assistant')) # Show event in GUI

    ai_response = thinking.get_ai_response(system_prompt, conversation_history)
    gui_output_queue.put((f"Kim Young-mi: {ai_response}", 'assistant'))
    speaking.speak(ai_response)

    conversation_history.append({"role": "system", "content": system_prompt})
    conversation_history.append({"role": "assistant", "content": ai_response})

def game_state_manager():
    """The core logic loop. Manages state and triggers context-appropriate events."""
    global app_running, current_game_state, last_game_state
    print("Game State Manager started.")
    match_data_loaded = False

    while app_running:
        current_game_state = game_awareness.get_current_screen()

        if current_game_state != last_game_state:
            print(f"STATE CHANGE: Moving from '{last_game_state}' to '{current_game_state}'")
            details = f"You have just navigated to the {current_game_state} screen."
            if current_game_state == "STORE": details = "You've just entered the store. Comment on what you see, or ask your boyfriend if he likes any of the skins."
            elif current_game_state == "BATTLEPASS": details = "You're now looking at the Battlepass. Ask your boyfriend about his progress or if there are any cool rewards."
            elif current_game_state == "AGENT_SELECT": details = "You are now in Agent Select. Comment on the team composition or ask your boyfriend who he is planning to play."
            elif current_game_state == "HOME": details = "You're back on the home screen."
            trigger_ai_reaction(f"SCREEN_CHANGED_TO_{current_game_state}", details, is_game_event=False)
            last_game_state = current_game_state
            if current_game_state != "IN_MATCH": match_data_loaded = False

        if current_game_state == "IN_MATCH":
            if not match_data_loaded:
                agents = game_awareness.detect_agents_in_match()
                game_data.load_data_for_agents(agents)
                match_data_loaded = True
            if game_awareness.check_for_kill(): trigger_ai_reaction("PLAYER_KILL", is_game_event=True)
            if game_awareness.check_for_death(): trigger_ai_reaction("PLAYER_DEATH", is_game_event=True)
            round_status = game_awareness.check_round_end()
            if round_status: trigger_ai_reaction(f"ROUND_{round_status}", is_game_event=True)
            ability_used = game_awareness.check_for_ability_use()
            if ability_used: trigger_ai_reaction("ABILITY_USED", event_details=f"The ability '{ability_used}' was just used.", is_game_event=True)

        sleep_time = 2 if current_game_state == "IN_MATCH" else 5
        time.sleep(sleep_time)

def user_conversation_handler():
    """A background thread that handles both voice and text input from the user."""
    global last_user_interaction_time
    print("User Conversation Handler started.")
    while app_running:
        user_input = None
        # Check for text input first
        try:
            user_input = gui_input_queue.get_nowait()
            print(f"Text input received: {user_input}")
        except queue.Empty:
            # If no text input, check for voice input
            # For now, we'll disable voice listening to focus on GUI testing.
            # To re-enable, simply uncomment the line below.
            # user_input = listening.listen_for_command()
            pass

        if user_input:
            last_user_interaction_time = time.time()
            gui_output_queue.put((f"You: {user_input}", 'user'))

            ai_response = thinking.get_ai_response(user_input, conversation_history)
            gui_output_queue.put((f"Kim Young-mi: {ai_response}", 'assistant'))
            speaking.speak(ai_response)

            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": ai_response})
        time.sleep(0.1)

def main():
    global app_running
    print("Starting Kim Young-mi AI (V3 - With GUI)...")

    # Initialization
    thinking.load_character_sheet()
    speaking.initialize_tts()

    print("\n--- Instructions ---")
    print("A chat window will open. You can type to her there.")
    print("The main application will continue to run in this terminal.")
    print("--------------------\n")

    # Start the GUI in a separate thread
    chat_gui.start_gui_thread(gui_input_queue, gui_output_queue)

    # Start background threads for game state and conversation
    state_thread = threading.Thread(target=game_state_manager, daemon=True)
    conv_thread = threading.Thread(target=user_conversation_handler, daemon=True)

    state_thread.start()
    conv_thread.start()

    try:
        # Keep the main thread alive to wait for the GUI to close
        # This is a bit of a hack; a more robust app would handle the GUI closing event.
        while state_thread.is_alive() and conv_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Kim Young-mi AI via Ctrl+C...")
    finally:
        app_running = False
        print("Goodbye.")

if __name__ == "__main__":
    main()