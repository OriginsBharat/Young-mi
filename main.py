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

# A shared state object for threads to communicate
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
    # These would be tuned based on the game's UI layout
    player_list_roi = (50, 200, 300, 400) # Placeholder for player list on the side

    while not stop_event.is_set():
        screen = perception_service.capture_screen()
        if screen is None:
            time.sleep(2) # Wait longer if screen capture fails
            continue

        # 1. Determine the current screen using templates
        detected_screen = perception_service.find_all_templates_on_screen(screen)

        # 2. Determine if the user is alone by reading the player list
        player_list_text = perception_service.ocr_region(screen, player_list_roi)

        # A simple check: if the user's name is the only one we can clearly identify,
        # or if the list is very short, assume they are alone.
        is_alone = False
        if player_list_text:
            # Count occurrences of the user's name. A more robust solution would be needed
            # for names that are substrings of others, but this is a solid start.
            if player_list_text.count(valorant_username) <= 1 and len(player_list_text.split('\n')) <= 2:
                 is_alone = True

        # Update shared state in a thread-safe way
        with shared_game_state["lock"]:
            shared_game_state["current_screen"] = detected_screen
            shared_game_state["is_alone"] = is_alone

        time.sleep(2) # Check screen state every 2 seconds

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
    perception_thread = threading.Thread(target=perception_loop, args=(perception, VALORANT_USERNAME, stop_event))
    perception_thread.start()

    try:
        print(f"\n--- Kim Young-mi is active. Hold '{PUSH_TO_TALK_KEY}' to speak. ---")
        while True:
            if keyboard.is_pressed(PUSH_TO_TALK_KEY):
                user_input = voice.listen()
                if user_input:
                    with shared_game_state["lock"]:
                        # Copy the state to avoid holding the lock during the AI call
                        current_context = shared_game_state.copy()

                    response = ai.generate_response(user_input, game_context=current_context)
                    voice.speak(response)
                else:
                    voice.speak("Sorry, I didn't catch that. Could you say it again?")

                while keyboard.is_pressed(PUSH_TO_TALK_KEY):
                    time.sleep(0.1)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n--- Shutting down... ---")
        voice.speak("Okay, I'm shutting down. See you next time, baby.")
    finally:
        stop_event.set()
        perception_thread.join()
        print("--- Kim Young-mi is offline. ---")

if __name__ == "__main__":
    main()