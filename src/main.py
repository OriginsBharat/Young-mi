import time
import threading
from dotenv import load_dotenv
import collections
import queue
from datetime import datetime
from pynput import keyboard

# Import all custom modules
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
time_since_last_session = None
initial_greeting_given = False

# --- V8: Inner Monologue ---
# A queue to hold her silent thoughts. maxsize=1 means it only holds the most recent thought.
thought_buffer = queue.Queue(maxsize=1)

# Communication queues for the GUI
gui_input_queue = queue.Queue()
gui_output_queue = queue.Queue()

# --- Hotkey State ---
TEAM_CHAT_HOTKEY = {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('v')}
current_hotkeys = set()

def screen_change_detector():
    """Monitors for screen changes and triggers high-level reactions."""
    global app_running, current_game_state, last_game_state, initial_greeting_given
    print("Screen Change Detector started.")

    while app_running:
        current_game_state = game_awareness.get_current_screen()

        # Handle the one-time, time-aware greeting
        if not initial_greeting_given and time_since_last_session and (current_game_state == "HOME" or current_game_state == "AGENT_SELECT"):
            print("First time seeing game this session. Triggering time-aware greeting.")
            details = (f"It has been {time_since_last_session} since you last saw your boyfriend. "
                       "He just launched Valorant. Greet him in your unique, loving, and teasing way.")
            # This is a direct interaction, not a buffered thought
            ai_response = thinking.get_ai_response(f"[Game Event: FIRST_GREETING_OF_SESSION. {details}]", conversation_history)
            gui_output_queue.put((f"Kim Young-mi: {ai_response}", 'assistant'))
            speaking.speak(ai_response)
            conversation_history.append({"role": "assistant", "content": ai_response})
            initial_greeting_given = True
            last_game_state = current_game_state

        # Handle reactions to changing menus
        if current_game_state != last_game_state:
            print(f"STATE CHANGE: Moving from '{last_game_state}' to '{current_game_state}'")
            details = f"You have just navigated to the {current_game_state} screen."
            if current_game_state == "STORE": details = "You've just entered the store. Comment on what you see, or ask your boyfriend if he likes any of the skins."
            elif current_game_state == "BATTLEPASS": details = "You're now looking at the Battlepass. Ask your boyfriend about his progress."
            elif current_game_state == "AGENT_SELECT": details = "You are now in Agent Select. Comment on the team composition."

            # This is also a direct interaction
            ai_response = thinking.get_ai_response(f"[Game Event: SCREEN_CHANGED_TO_{current_game_state}. {details}]", conversation_history)
            gui_output_queue.put((f"Kim Young-mi: {ai_response}", 'assistant'))
            speaking.speak(ai_response)
            conversation_history.append({"role": "assistant", "content": ai_response})
            last_game_state = current_game_state

        time.sleep(5) # Check for screen changes less frequently

def inner_monologue_handler():
    """A background thread that 'thinks' about the game state without speaking."""
    print("Inner Monologue started.")
    last_event_context = ""
    while app_running:
        if current_game_state == "IN_MATCH":
            try:
                game_context = game_awareness.get_current_game_context()
                current_event_context = f"{game_context['score']}|{game_context['players_alive']}"

                # Only generate a new thought if the game state has changed
                if current_event_context != last_event_context:
                    last_event_context = current_event_context
                    prompt = (f"[Internal Thought: The current game state is: Score {game_context['score']}, Players Alive {game_context['players_alive']}. "
                              f"What is a brief, insightful, tactical observation about this situation? Frame it as a thought you might share with your boyfriend.]")

                    # Generate the thought silently, with no conversation history
                    tactical_thought = thinking.get_ai_response(prompt, [])

                    # Clear the buffer and put the new thought in
                    if not thought_buffer.empty():
                        try: thought_buffer.get_nowait()
                        except queue.Empty: pass
                    thought_buffer.put(tactical_thought)
                    print(f"  -> Inner Monologue generated new thought: {tactical_thought}")
            except Exception as e:
                print(f"Error in inner monologue: {e}")
        time.sleep(5) # Analyze the game state periodically

def user_conversation_handler():
    """Handles voice/text input and speaks from the thought buffer during lulls."""
    global last_user_interaction_time
    print("User Conversation Handler started.")
    while app_running:
        user_input = None
        try:
            user_input = gui_input_queue.get_nowait()
        except queue.Empty:
            user_input = listening.listen_for_command()

        if user_input:
            last_user_interaction_time = time.time()
            gui_output_queue.put((f"You: {user_input}", 'user'))
            ai_response = thinking.get_ai_response(user_input, conversation_history)
            gui_output_queue.put((f"Kim Young-mi: {ai_response}", 'assistant'))
            speaking.speak(ai_response)
            conversation_history.extend([{"role": "user", "content": user_input}, {"role": "assistant", "content": ai_response}])
        else:
            # This is a conversational lull. Check for a thought to speak.
            if time.time() - last_user_interaction_time > 10: # Only speak if it's been quiet for 10s
                try:
                    thought_to_speak = thought_buffer.get_nowait()
                    if thought_to_speak:
                        print(f"--- Speaking buffered thought: {thought_to_speak} ---")
                        gui_output_queue.put((f"Kim Young-mi: {thought_to_speak}", 'assistant'))
                        speaking.speak(thought_to_speak)
                        conversation_history.append({"role": "assistant", "content": thought_to_speak})
                        last_user_interaction_time = time.time() # Reset timer after she speaks
                except queue.Empty:
                    pass
        time.sleep(0.1)

def personality_learning_handler():
    """Periodically triggers the personality learning process."""
    # ... (This function remains the same) ...

def on_hotkey_press(key):
    """Callback for hotkey presses."""
    if key in TEAM_CHAT_HOTKEY:
        current_hotkeys.add(key)
        if all(k in current_hotkeys for k in TEAM_CHAT_HOTKEY):
            speaking.toggle_team_chat()

def on_hotkey_release(key):
    """Callback for hotkey releases."""
    try: current_hotkeys.remove(key)
    except KeyError: pass

def main():
    global app_running, conversation_history, time_since_last_session
    print("Starting Kim Young-mi AI (V8 - The Inner Monologue)...")

    memory_manager.initialize_memory()
    thinking.load_character_sheet()
    speaking.initialize_tts()

    last_seen = memory_manager.retrieve_metadata("last_seen")
    if last_seen:
        # ... (Time calculation logic remains the same) ...

    conversation_history = memory_manager.retrieve_conversation()
    for msg in conversation_history:
        # ... (GUI history loading remains the same) ...

    # Start all threads
    chat_gui.start_gui_thread(gui_input_queue, gui_output_queue)
    threading.Thread(target=screen_change_detector, daemon=True).start()
    threading.Thread(target=inner_monologue_handler, daemon=True).start()
    threading.Thread(target=user_conversation_handler, daemon=True).start()
    threading.Thread(target=personality_learning_handler, daemon=True).start()

    hotkey_listener = keyboard.Listener(on_press=on_hotkey_press, on_release=on_hotkey_release)
    hotkey_listener.start()

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        app_running = False
        hotkey_listener.stop()
        memory_manager.save_conversation(conversation_history)
        memory_manager.save_metadata("last_seen", int(time.time()))
        print("Goodbye.")

if __name__ == "__main__":
    main()