# main.py
# This is the main entry point for the application.
# It orchestrates all modules into a responsive, asynchronous application.

import time
import keyboard
import os
import threading
import queue
from dotenv import load_dotenv
from src.ai_core import AICore
from src.screen_perception import ScreenPerception
from src.voice_io import VoiceIO
from src.gui import ChatWindow

# A thread-safe object to store the current game state
shared_game_state = {
    "is_alone": True,
    "current_screen": "Unknown",
    "lock": threading.Lock()
}

# --- Background "Inner Monologue" Thread ---
def inner_monologue_loop(ai_core, thought_queue, stop_event):
    """
    A separate thread that periodically prompts the AI to "think" about the current
    game state, generating proactive thoughts.
    """
    print("[Inner Monologue Thread] Started.")
    while not stop_event.is_set():
        time.sleep(20) # Think every 20 seconds

        with shared_game_state["lock"]:
            current_context = shared_game_state.copy()

        # We don't want her talking to herself if the game isn't even running
        if current_context["current_screen"] != "Unknown":
            thought = ai_core.generate_thought(current_context)
            if thought:
                thought_queue.put(thought)

    print("[Inner Monologue Thread] Stopped.")


def main():
    """
    Main function to run the Kim Young-mi AI companion.
    """
    load_dotenv()
    PUSH_TO_TALK_KEY = os.getenv("PUSH_TO_TALK_KEY", "caps lock")
    VOICE_CLONE_PATH = os.getenv("VOICE_CLONE_PATH")
    VALORANT_USERNAME = os.getenv("VALORANT_USERNAME", "")

    print("--- Initializing Kim Young-mi ---")

    # --- Communication Queues ---
    gui_input_queue = queue.Queue()
    gui_output_queue = queue.Queue()
    thought_queue = queue.Queue()

    # --- Module Initialization & Thread Start ---
    stop_event = threading.Event()

    ai = AICore()
    voice = VoiceIO(voice_clone_path=VOICE_CLONE_PATH)
    voice.start()

    perception_thread = ScreenPerception(
        shared_state=shared_game_state,
        valorant_username=VALORANT_USERNAME,
        stop_event=stop_event
    )
    perception_thread.start()

    gui_thread = ChatWindow(gui_input_queue, gui_output_queue)
    gui_thread.start()

    # Start the Inner Monologue thread
    monologue_thread = threading.Thread(target=inner_monologue_loop, args=(ai, thought_queue, stop_event), daemon=True)
    monologue_thread.start()

    voice.speak("I'm awake and watching. Let's play, babe.")
    gui_output_queue.put("I'm awake and watching. Let's play, babe.")

    # --- Main Application Loop (Proactive & Asynchronous) ---
    is_recording = False
    audio_buffer = []
    last_interaction_time = time.time()
    LULL_DURATION = 15 # Seconds before she might speak a thought

    try:
        print(f"\n--- Kim Young-mi is active. Hold '{PUSH_TO_TALK_KEY}' to speak, or type in the chat window. ---")
        while not stop_event.is_set():
            user_input = None

            # 1. Check for text input from GUI
            try:
                user_input = gui_input_queue.get_nowait()
            except queue.Empty:
                pass

            # 2. Check for voice input
            if keyboard.is_pressed(PUSH_TO_TALK_KEY):
                if not is_recording:
                    print("Recording...")
                    is_recording = True
                    audio_buffer.clear()
                try:
                    audio_buffer.append(voice.audio_queue.get_nowait())
                except queue.Empty:
                    pass
            elif is_recording:
                is_recording = False
                print("Processing voice input...")
                user_input = voice.recognize_audio(audio_buffer)

            # 3. Process user input if it exists
            if user_input:
                last_interaction_time = time.time() # Reset lull timer on user input
                with shared_game_state["lock"]:
                    current_context = shared_game_state.copy()
                response = ai.generate_response(user_input, game_context=current_context)
                voice.speak(response)
                gui_output_queue.put(response)
                last_interaction_time = time.time() # Also reset after she speaks

            # 4. If there's no user input, check for a conversational lull
            elif time.time() - last_interaction_time > LULL_DURATION:
                try:
                    # Check for a new thought from the inner monologue
                    thought = thought_queue.get_nowait()
                    print(f"[Natural Interjection] Speaking thought: {thought}")
                    voice.speak(thought)
                    gui_output_queue.put(thought)
                    ai.add_ai_thought_to_history(thought)
                    last_interaction_time = time.time() # Reset timer after she speaks
                except queue.Empty:
                    pass # No thoughts to speak, continue silently

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n--- Shutting down... ---")
        voice.speak("Okay, I'm shutting down. See you next time, babe.")
    finally:
        stop_event.set()
        voice.stop()
        perception_thread.join()
        monologue_thread.join()
        voice.join()
        print("--- Kim Young-mi is offline. ---")

if __name__ == "__main__":
    main()