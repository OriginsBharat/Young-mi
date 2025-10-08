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
# This is a simple way to pass data between the perception and main threads.
shared_game_state = {
    "last_kill": None,
    "round_outcome": None,
    "current_screen": "Unknown",
    "lock": threading.Lock() # To prevent race conditions when updating the state
}

# --- Background Perception Thread ---
def perception_loop(perception_service, stop_event):
    """
    A separate thread that continuously watches the screen to understand the game state.
    """
    print("[Perception Thread] Started.")
    # Define placeholder ROIs (Regions of Interest) for a 1920x1080 screen.
    # These would need to be configurable in a real application.
    # (x, y, width, height)
    kill_feed_roi = (1500, 150, 400, 200)

    last_kill_text = ""

    while not stop_event.is_set():
        # Capture the screen
        screen = perception_service.capture_screen()
        if screen is None:
            time.sleep(1)
            continue

        # 1. Check for round end banners
        victory_found = perception_service.find_template_on_screen(screen, 'data/templates/victory_banner.png')
        defeat_found = perception_service.find_template_on_screen(screen, 'data/templates/defeat_banner.png')

        # 2. Check for new kills in the kill feed
        current_kill_text = perception_service.ocr_region(screen, kill_feed_roi)

        # Update shared state in a thread-safe way
        with shared_game_state["lock"]:
            if victory_found:
                shared_game_state["round_outcome"] = "VICTORY"
            elif defeat_found:
                shared_game_state["round_outcome"] = "DEFEAT"
            else:
                # Reset if no banner is found
                shared_game_state["round_outcome"] = None

            if current_kill_text and current_kill_text != last_kill_text:
                # A simple way to detect a new kill is if the OCR text changes.
                shared_game_state["last_kill"] = current_kill_text
                last_kill_text = current_kill_text

        # The loop will run approximately every 1 second
        time.sleep(1)

    print("[Perception Thread] Stopped.")


def main():
    """
    Main function to run the Kim Young-mi AI companion.
    """
    # --- Configuration and Initialization ---
    load_dotenv()
    PUSH_TO_TALK_KEY = os.getenv("PUSH_TO_TALK_KEY", "caps lock")
    VOICE_CLONE_PATH = os.getenv("VOICE_CLONE_PATH")

    print("--- Initializing Kim Young-mi ---")
    ai = AICore()
    perception = ScreenPerception()
    voice = VoiceIO(voice_clone_path=VOICE_CLONE_PATH)

    # --- Wait for Valorant to Start ---
    print("\nWaiting for Valorant to start... (VALORANT.exe)")
    while not perception.is_valorant_running():
        time.sleep(5)

    voice.speak("Valorant detected! Hey babe, I'm here. Let's play.")

    # --- Start the Perception Thread ---
    stop_event = threading.Event()
    perception_thread = threading.Thread(target=perception_loop, args=(perception, stop_event))
    perception_thread.start()

    # --- Main Application Loop (Handles Voice Interaction) ---
    try:
        print(f"\n--- Kim Young-mi is active. Hold '{PUSH_TO_TALK_KEY}' to speak. ---")
        while True:
            if keyboard.is_pressed(PUSH_TO_TALK_KEY):
                user_input = voice.listen()

                if user_input:
                    # Read the latest game state from the shared object
                    with shared_game_state["lock"]:
                        game_context = f"Current Screen: {shared_game_state['current_screen']}, Last Kill: {shared_game_state['last_kill']}, Round Outcome: {shared_game_state['round_outcome']}"

                    response = ai.generate_response(user_input, game_context=game_context)
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
        # --- Cleanup ---
        stop_event.set()
        perception_thread.join() # Wait for the perception thread to finish
        print("--- Kim Young-mi is offline. ---")


if __name__ == "__main__":
    main()