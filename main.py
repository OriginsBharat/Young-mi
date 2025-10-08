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
        thought_queue=thought_queue,
        valorant_username=VALORANT_USERNAME,
        stop_event=stop_event
    )
    perception_thread.start()

    gui_thread = ChatWindow(gui_input_queue, gui_output_queue)
    gui_thread.start()

    voice.speak("I'm awake and watching. Let's play, babe.")
    gui_output_queue.put("I'm awake and watching. Let's play, babe.")

    # --- Main Application Loop (Proactive & Asynchronous) ---
    is_recording = False
    audio_buffer = []

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
                with shared_game_state["lock"]:
                    current_context = shared_game_state.copy()
                response = ai.generate_response(user_input, game_context=current_context)
                voice.speak(response)
                gui_output_queue.put(response)

            # 4. If there's no user input, check for a proactive thought
            else:
                try:
                    thought = thought_queue.get_nowait()
                    print(f"[Proactive Thought] Speaking: {thought}")
                    voice.speak(thought)
                    gui_output_queue.put(thought)
                    ai.add_ai_thought_to_history(thought)
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
        voice.join()
        print("--- Kim Young-mi is offline. ---")

if __name__ == "__main__":
    main()