# main.py
# This is the main entry point for the application.
# It orchestrates the AI core, memory, screen perception, and voice I/O.

import time
import keyboard
import os
import threading
from dotenv import load_dotenv
from src.ai_core import AICore
from src.screen_perception import ScreenPerception
from src.voice_io import VoiceIO

# A thread-safe object to store the current game state, passed between threads
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
    ai = AICore()
    voice = VoiceIO(voice_clone_path=VOICE_CLONE_PATH)

    # --- Start the Perception Thread ---
    # The new ScreenPerception class is a thread itself. We instantiate it and start it.
    stop_event = threading.Event()
    perception_thread = ScreenPerception(
        shared_state=shared_game_state,
        valorant_username=VALORANT_USERNAME,
        stop_event=stop_event
    )
    perception_thread.start()

    voice.speak("I'm awake and watching. Let's play, babe.")

    # --- Main Application Loop (Handles Voice Interaction) ---
    try:
        print(f"\n--- Kim Young-mi is active. Hold '{PUSH_TO_TALK_KEY}' to speak. ---")
        while True:
            if keyboard.is_pressed(PUSH_TO_TALK_KEY):
                user_input = voice.listen()

                # Wait for the key to be released *before* processing and responding
                # This prevents the loop from re-triggering while the user is still holding the key.
                while keyboard.is_pressed(PUSH_TO_TALK_KEY):
                    time.sleep(0.05)

                if user_input:
                    with shared_game_state["lock"]:
                        # Make a copy of the state to avoid holding the lock during the AI call
                        current_context = shared_game_state.copy()

                    response = ai.generate_response(user_input, game_context=current_context)
                    voice.speak(response)
                else:
                    voice.speak("Sorry, baby, I didn't quite catch that. Could you say it again?")
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n--- Shutting down... ---")
        voice.speak("Okay, I'm shutting down. See you next time, babe.")
    finally:
        # --- Cleanup ---
        stop_event.set()
        perception_thread.join() # Wait for the perception thread to finish cleanly
        print("--- Kim Young-mi is offline. ---")

if __name__ == "__main__":
    main()