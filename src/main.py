import time
import threading
from dotenv import load_dotenv
import collections
import queue
from datetime import datetime
from pynput import keyboard
import re

# Import all custom modules
import src.thinking as thinking
import src.speaking as speaking
import src.listening as listening
import src.game_awareness as game_awareness
import src.game_data as game_data
import src.chat_gui as chat_gui
import src.memory_manager as memory_manager
import src.personality_learner as personality_learner
import src.web_search as web_search

# Load environment variables
load_dotenv()

# --- Global State & Configuration ---
app_running = True
conversation_history = []
current_game_state = "UNKNOWN"
last_user_interaction_time = 0
time_since_last_session = None
initial_greeting_given = False

thought_buffer = queue.Queue(maxsize=1)
gui_input_queue = queue.Queue()
gui_output_queue = queue.Queue()

TEAM_CHAT_HOTKEY = {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('v')}
current_hotkeys = set()

# --- Core Application Threads ---

def screen_change_handler():
    """Monitors for screen changes and triggers high-level, direct reactions."""
    global current_game_state, initial_greeting_given
    last_screen = "UNKNOWN"

    while app_running:
        current_game_state = game_awareness.get_current_screen()

        if current_game_state != last_screen:
            print(f"STATE CHANGE: Moving to '{current_game_state}'")

            # V9: Greet the user the first time the game is seen this session
            if not initial_greeting_given and time_since_last_session and (current_game_state in ["HOME", "AGENT_SELECT"]):
                initial_greeting_given = True
                details = (f"It has been {time_since_last_session} since you last saw your boyfriend. "
                           "He just launched Valorant. Greet him in your unique, loving, and teasing way.")
                ai_response = thinking.get_ai_response(f"[Game Event: FIRST_GREETING_OF_SESSION. {details}]", [])
                gui_output_queue.put((f"Kim Young-mi: {ai_response}", 'assistant'))
                speaking.speak(ai_response)
                conversation_history.append({"role": "assistant", "content": ai_response})

            # Handle menu-change commentary
            elif last_screen != "UNKNOWN": # Don't comment on the very first screen detection
                details = f"You have just navigated to the {current_game_state} screen."
                if current_game_state == "STORE": details = "You've just entered the store. Comment on what you see, or ask your boyfriend if he likes any of the skins."
                elif current_game_state == "BATTLEPASS": details = "You're now looking at the Battlepass. Ask your boyfriend about his progress."
                elif current_game_state == "AGENT_SELECT": details = "You are now in Agent Select. Comment on the team composition."

                ai_response = thinking.get_ai_response(f"[Game Event: SCREEN_CHANGED_TO_{current_game_state}. {details}]", conversation_history)
                gui_output_queue.put((f"Kim Young-mi: {ai_response}", 'assistant'))
                speaking.speak(ai_response)
                conversation_history.append({"role": "assistant", "content": ai_response})

            last_screen = current_game_state
        time.sleep(3)

def inner_monologue_handler():
    """V9: The true 'commentator brain'. Silently watches for all in-match events and generates thoughts."""
    print("Inner Monologue (Commentator Brain) started.")
    event_cooldowns = collections.defaultdict(float)
    COOLDOWN_DURATION = 10

    while app_running:
        if current_game_state == "IN_MATCH":
            try:
                now = time.time()
                game_context = game_awareness.get_current_game_context()
                context_details = f"The score is {game_context['score']} and players alive are {game_context['players_alive']}."
                event_type, event_prompt_details = None, ""

                # --- Restore event detection ---
                if now - event_cooldowns["kill"] > COOLDOWN_DURATION and game_awareness.check_for_kill():
                    event_type, event_prompt_details = "PLAYER_KILL", f"You just got a kill. {context_details}"
                elif now - event_cooldowns["death"] > COOLDOWN_DURATION and game_awareness.check_for_death():
                    event_type, event_prompt_details = "PLAYER_DEATH", f"You just died. {context_details}"
                elif now - event_cooldowns["round_end"] > (COOLDOWN_DURATION * 2): # Longer cooldown for round end
                    round_status = game_awareness.check_round_end()
                    if round_status: event_type, event_prompt_details = f"ROUND_{round_status}", context_details

                if event_type:
                    event_cooldowns[event_type.lower()] = now
                    prompt = (f"[Internal Thought: Game Event: {event_type}. {event_prompt_details}. "
                              f"Provide a brief, insightful, in-character tactical observation or reaction.]")

                    tactical_thought = thinking.get_ai_response(prompt, [])
                    if not thought_buffer.empty():
                        try: thought_buffer.get_nowait()
                        except queue.Empty: pass
                    thought_buffer.put(tactical_thought)
                    print(f"  -> Inner Monologue generated new thought: {tactical_thought}")
            except Exception as e:
                print(f"Error in inner monologue: {e}")
        time.sleep(2)

def user_conversation_handler():
    """Handles all direct user interaction and speaks buffered thoughts."""
    global last_user_interaction_time
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
            if time.time() - last_user_interaction_time > 15: # Conversational lull
                try:
                    thought_to_speak = thought_buffer.get_nowait()
                    if thought_to_speak:
                        print(f"--- Speaking buffered thought: {thought_to_speak} ---")
                        gui_output_queue.put((f"Kim Young-mi: {thought_to_speak}", 'assistant'))
                        speaking.speak(thought_to_speak)
                        conversation_history.append({"role": "assistant", "content": thought_to_speak})
                        last_user_interaction_time = time.time()
                except queue.Empty: pass
        time.sleep(0.1)

def curiosity_handler():
    """Autonomously learns about new things seen on screen."""
    while app_running:
        time.sleep(120) # Check for new things to learn every 2 minutes
        try:
            all_text = game_awareness.get_all_text_on_screen()
            potential_topics = set(re.findall(r'\b[A-Z][a-z]{3,}\b', all_text))
            for topic in potential_topics:
                if not memory_manager.is_word_known(topic):
                    is_relevant_prompt = f"Is '{topic}' a known agent, map, ability, or general term in the game Valorant? Answer with a single word: YES or NO."
                    relevance_check = thinking.get_ai_response(is_relevant_prompt, [])
                    if "YES" in relevance_check.upper():
                        summary = web_search.search_and_summarize(f"What is {topic} in Valorant?")
                        memory_manager.add_learned_fact(topic, summary)
                    else:
                        memory_manager.add_known_word(topic)
        except Exception as e:
            print(f"Error in curiosity handler: {e}")

def personality_learning_handler():
    """Periodically triggers the personality learning process."""
    while app_running:
        time.sleep(86400) # 24 hours
        if app_running:
            personality_learner.digest_all_memories()
            thinking.load_character_sheet()
            gui_output_queue.put(("[SYSTEM] I've just reflected on our recent conversations.", 'assistant'))

def on_hotkey_press(key):
    if key in TEAM_CHAT_HOTKEY:
        current_hotkeys.add(key)
        if all(k in current_hotkeys for k in TEAM_CHAT_HOTKEY):
            speaking.toggle_team_chat()

def on_hotkey_release(key):
    try: current_hotkeys.remove(key)
    except KeyError: pass

def main():
    """Initializes and runs all application threads."""
    global app_running, conversation_history, time_since_last_session
    print("Starting Kim Young-mi AI (V9 - The Autonomous Soul)...")

    memory_manager.initialize_memory()
    thinking.load_character_sheet()
    speaking.initialize_tts()

    last_seen = memory_manager.retrieve_metadata("last_seen")
    if last_seen:
        time_passed = time.time() - int(last_seen)
        # ... (Time calculation logic) ...

    conversation_history = memory_manager.retrieve_conversation()
    for msg in conversation_history:
        # ... (GUI history loading) ...

    threads = [
        threading.Thread(target=chat_gui.start_gui_thread, args=(gui_input_queue, gui_output_queue)),
        threading.Thread(target=screen_change_handler),
        threading.Thread(target=inner_monologue_handler),
        threading.Thread(target=user_conversation_handler),
        threading.Thread(target=personality_learning_handler),
        threading.Thread(target=curiosity_handler)
    ]
    for t in threads: t.daemon = True; t.start()

    hotkey_listener = keyboard.Listener(on_press=on_hotkey_press, on_release=on_hotkey_release)
    hotkey_listener.start()

    try:
        hotkey_listener.join()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        app_running = False
        memory_manager.save_conversation(conversation_history)
        memory_manager.save_metadata("last_seen", int(time.time()))
        print("Goodbye.")

if __name__ == "__main__":
    main()