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

    # --- Module Initialization & Thread Start ---
    stop_event = threading.Event()

    ai = AICore()
    voice = VoiceIO(voice_clone_path=VOICE_CLONE_PATH)
    voice.start() # Start the non-blocking audio input stream

    perception_thread = ScreenPerception(
        shared_state=shared_game_state,
        valorant_username=VALORANT_USERNAME,
        stop_event=stop_event
    )
    perception_thread.start()

    gui_thread = ChatWindow(gui_input_queue, gui_output_queue)
    gui_thread.start()

    voice.speak("I'm awake and watching. Let's play, babe.")
    gui_output_queue.put("I'm awake and watching. Let's play, babe.")

    # --- Main Application Loop (Asynchronous Input Handling) ---
    is_recording = False
    audio_buffer = []

    try:
        print(f"\n--- Kim Young-mi is active. Hold '{PUSH_TO_TALK_KEY}' to speak, or type in the chat window. ---")
        while not stop_event.is_set():
            # 1. Check for text input from the GUI (non-blocking)
            try:
                user_input = gui_input_queue.get_nowait()
                if user_input:
                    # Process text input immediately
                    with shared_game_state["lock"]:
                        current_context = shared_game_state.copy()
                    response = ai.generate_response(user_input, game_context=current_context)
                    voice.speak(response)
                    gui_output_queue.put(response)
            except queue.Empty:
                pass

            # 2. Check for voice input state (non-blocking)
            if keyboard.is_pressed(PUSH_TO_TALK_KEY):
                if not is_recording:
                    print("Recording...")
                    is_recording = True
                    audio_buffer.clear() # Clear buffer for new recording
                # Collect audio data from the queue
                try:
                    audio_chunk = voice.audio_queue.get_nowait()
                    audio_buffer.append(audio_chunk)
                except queue.Empty:
                    pass
            elif is_recording:
                # Key was just released, process the recorded audio
                print("Processing voice input...")
                is_recording = False
                user_input = voice.recognize_audio(audio_buffer)
                if user_input:
                    with shared_game_state["lock"]:
                        current_context = shared_game_state.copy()
                    response = ai.generate_response(user_input, game_context=current_context)
                    voice.speak(response)
                    gui_output_queue.put(response)
                else:
                    voice.speak("Sorry, baby, I didn't quite catch that.")
                    gui_output_queue.put("Sorry, baby, I didn't quite catch that.")

            time.sleep(0.05) # Keeps the loop responsive without high CPU usage

    except KeyboardInterrupt:
        print("\n--- Shutting down... ---")
        voice.speak("Okay, I'm shutting down. See you next time, babe.")
    finally:
        # --- Cleanup ---
        stop_event.set()
        voice.stop()
        perception_thread.join()
        voice.join()
        # GUI thread is a daemon, so it will exit automatically
        print("--- Kim Young-mi is offline. ---")

if __name__ == "__main__":
    main()