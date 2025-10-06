import time
import threading
from dotenv import load_dotenv
import collections
import queue
from datetime import datetime

# Import our custom modules
import src.thinking as thinking
import src.speaking as speaking
import src.listening as listening
import src.game_awareness as game_awareness
import src.game_data as game_data
import src.chat_gui as chat_gui
import src.memory_manager as memory_manager
import src.personality_learner as personality_learner

# Load environment variables
load_dotenv()

# --- Global State & Configuration ---
app_running = True
conversation_history = []
current_game_state = "UNKNOWN"
last_game_state = "UNKNOWN"
last_user_interaction_time = 0
USER_ID = "kim_young_mi_user"
time_since_last_session = None # V5: For the natural greeting
initial_greeting_given = False # V5: Flag to ensure greeting only happens once

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
        return

    for event, timestamp in recent_events:
        if event == event_type and (current_time - timestamp) < EVENT_COOLDOWN:
            return

    recent_events.append((event_type, current_time))

    system_prompt = f"[Game Event: {event_type}. {event_details}]"
    print(f"--- New Game Event Detected: {system_prompt} ---")
    gui_output_queue.put((f"[{event_type}]", 'assistant'))

    ai_response = thinking.get_ai_response(system_prompt, conversation_history)
    gui_output_queue.put((f"Kim Young-mi: {ai_response}", 'assistant'))
    speaking.speak(ai_response)

    conversation_history.append({"role": "system", "content": system_prompt})
    conversation_history.append({"role": "assistant", "content": ai_response})

def game_state_manager():
    """The core logic loop. Manages state and triggers context-appropriate events."""
    global app_running, current_game_state, last_game_state, initial_greeting_given
    print("Game State Manager started.")
    match_data_loaded = False

    while app_running:
        current_game_state = game_awareness.get_current_screen()

        # V5: Special check for the first greeting of the session
        if not initial_greeting_given and time_since_last_session and (current_game_state == "HOME" or current_game_state == "AGENT_SELECT"):
            print("First time seeing game this session. Triggering time-aware greeting.")
            details = (f"It has been {time_since_last_session} since you last saw your boyfriend. "
                       "He just launched Valorant for the first time this session. "
                       "Greet him in your unique, loving, and teasing way based on this fact.")
            trigger_ai_reaction("FIRST_GREETING_OF_SESSION", details, is_game_event=False)
            initial_greeting_given = True
            last_game_state = current_game_state # Prevent a double reaction

        # --- State Change Logic ---
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
        try:
            user_input = gui_input_queue.get_nowait()
            if user_input: print(f"Text input received: {user_input}")
        except queue.Empty:
            user_input = listening.listen_for_command()
            if user_input: print(f"Voice input received: {user_input}")

        if user_input:
            last_user_interaction_time = time.time()
            gui_output_queue.put((f"You: {user_input}", 'user'))

            ai_response = thinking.get_ai_response(user_input, conversation_history)
            gui_output_queue.put((f"Kim Young-mi: {ai_response}", 'assistant'))
            speaking.speak(ai_response)

            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": ai_response})
        time.sleep(0.1)

def personality_learning_handler():
    """A background thread that periodically triggers the personality learning process."""
    print("Personality Learning Handler started.")
    while app_running:
        time.sleep(86400) # 24 hours
        if app_running:
            print("\n--- Starting Daily Personality Evolution ---")
            print("Saving current session before learning...")
            memory_manager.compress_and_save_conversation(USER_ID, conversation_history)
            personality_learner.digest_all_memories(USER_ID)
            print("Reloading character sheet with new memories...")
            thinking.load_character_sheet()
            gui_output_queue.put(("[SYSTEM] I've just reflected on our recent conversations.", 'assistant'))
            print("--- Personality Evolution Complete ---\n")

def main():
    global app_running, conversation_history, time_since_last_session
    print("Starting Kim Young-mi AI (V5 - The Invitation)...")

    # Initialization
    thinking.load_character_sheet()
    speaking.initialize_tts()

    if memory_manager.initialize_memory():
        # V5: Get the time since last session for the natural greeting
        last_seen = memory_manager.retrieve_last_seen_timestamp(USER_ID)
        if last_seen:
            time_now = datetime.now(last_seen.tzinfo)
            time_passed = time_now - last_seen

            # Make the time human-readable
            seconds = time_passed.total_seconds()
            if seconds < 120: # Less than 2 minutes
                time_since_last_session = "just a moment"
            elif seconds < 7200: # Less than 2 hours
                time_since_last_session = f"{int(seconds / 60)} minutes"
            elif seconds < 172800: # Less than 2 days
                time_since_last_session = f"{int(seconds / 3600)} hours"
            else:
                time_since_last_session = f"{int(seconds / 86400)} days"

        conversation_history = memory_manager.retrieve_and_decompress_last_conversation(USER_ID)
        for message in conversation_history:
            role = message.get("role")
            content = message.get("content")
            if role == "user": gui_output_queue.put((f"You: {content}", 'user'))
            elif role == "assistant": gui_output_queue.put((f"Kim Young-mi: {content}", 'assistant'))

    # Start all background threads
    chat_gui.start_gui_thread(gui_input_queue, gui_output_queue)
    state_thread = threading.Thread(target=game_state_manager, daemon=True)
    conv_thread = threading.Thread(target=user_conversation_handler, daemon=True)
    learning_thread = threading.Thread(target=target=personality_learning_handler, daemon=True)

    state_thread.start()
    conv_thread.start()
    learning_thread.start()

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Kim Young-mi AI via Ctrl+C...")
    finally:
        app_running = False
        print("Saving final conversation and timestamp to the cloud...")
        memory_manager.compress_and_save_conversation(USER_ID, conversation_history)
        memory_manager.save_last_seen_timestamp(USER_ID)
        print("Goodbye.")

if __name__ == "__main__":
    # The real entry point should now be the setup wizard.
    # This main function is run by `run_silent.pyw`.
    main()