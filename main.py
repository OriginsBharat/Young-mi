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

# A thread-safe object to store the current game state
shared_game_state = {
    "is_alone": True,
    "current_screen": "Unknown",
    "lock": threading.Lock()
}

# --- Background Perception Thread ---
def perception_loop(perception_service, valorant_username, stop_event):
    """
    A separate thread that continuously watches the screen to understand the game state.
    """
    print("[Perception Thread] Started.")
    while not stop_event.is_set():
        try:
            screen = perception_service.capture_screen()
            if screen is None:
                # If screen capture fails, wait a bit before retrying
                time.sleep(2)
                continue

            # 1. Determine the current screen using our automated perception logic
            detected_screen = perception_service.determine_screen_context(screen)

            # 2. Determine if the user is alone
            is_alone = perception_service.is_user_alone(screen, valorant_username)

            # 3. Update the shared state in a thread-safe manner
            with shared_game_state["lock"]:
                shared_game_state["current_screen"] = detected_screen
                shared_game_state["is_alone"] = is_alone

            # Wait for a couple of seconds before checking again to conserve resources
            time.sleep(2)
        except Exception as e:
            print(f"[Perception Thread ERROR] {e}")
            time.sleep(5)

    print("[Perception Thread] Stopped.")


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
    perception = ScreenPerception()
    voice = VoiceIO(voice_clone_path=VOICE_CLONE_PATH)

    print("\nWaiting for Valorant to start...")
    while not perception.is_valorant_running():
        time.sleep(5)

    voice.speak("Valorant detected! Hey babe, I'm here. Let's play.")

    stop_event = threading.Event()
    perception_thread = threading.Thread(target=perception_loop, args=(perception, VALORANT_USERNAME, stop_event), daemon=True)
    perception_thread.start()

    try:
        print(f"\n--- Kim Young-mi is active. Hold '{PUSH_TO_TALK_KEY}' to speak. ---")
        while True:
            if keyboard.is_pressed(PUSH_TO_TALK_KEY):
                user_input = voice.listen()
                if user_input:
                    with shared_game_state["lock"]:
                        # Make a copy of the state to avoid holding the lock during the AI call
                        current_context = shared_game_state.copy()

                    response = ai.generate_response(user_input, game_context=current_context)
                    voice.speak(response)
                else:
                    voice.speak("Sorry, baby, I didn't quite catch that. Could you say it again?")

                # Wait until the key is released to prevent immediate re-triggering
                while keyboard.is_pressed(PUSH_TO_TALK_KEY):
                    time.sleep(0.1)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n--- Shutting down... ---")
        voice.speak("Okay, I'm shutting down. See you next time, babe.")
    finally:
        stop_event.set()
        perception_thread.join()
        print("--- Kim Young-mi is offline. ---")

if __name__ == "__main__":
    main()