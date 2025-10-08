# teach_her.py
# This script is a guided wizard to help the user teach the AI how to recognize
# different screens in Valorant by capturing template images.

import keyboard
import time
import os
from src.screen_perception import ScreenPerception
import cv2

# --- Configuration ---
CAPTURE_KEY = 'f12'
TEMPLATES_DIR = "data/templates"

# --- Helper Functions ---
def clear_screen():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def select_roi(image):
    """Allows the user to select a Region of Interest (ROI) from an image."""
    print("\nA window will appear with your screenshot.")
    print("Drag your mouse to draw a rectangle around the unique element you want to teach her.")
    print("Press ENTER or SPACE when you are done.")
    roi = cv2.selectROI("Teaching Window", image)
    cv2.destroyWindow("Teaching Window")
    return roi

def run_teaching_wizard():
    """The main interactive wizard for teaching the AI."""
    clear_screen()
    print("--- Welcome to the Kim Young-mi Teaching Wizard ---")
    print("\nI will help you teach her how to recognize different screens in Valorant.")
    print("This will create a library of small template images based on your screen.")
    print("\nProcess:")
    print("1. I will ask you to go to a specific screen in the game (e.g., the Store).")
    print(f"2. Once you are there, press the '{CAPTURE_KEY}' key to take a screenshot.")
    print("3. A window will open. Drag a box around a UNIQUE part of that screen.")
    print("   (e.g., for the Store, select the word 'STORE' at the top of the screen).")
    print("4. You will be prompted to name this screen.")

    # Ensure the templates directory exists
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR)
        print(f"\nCreated templates directory at: {TEMPLATES_DIR}")

    perception = ScreenPerception()

    while True:
        print("\n-------------------------------------------------")
        screen_name = input("Enter a name for the new screen you want to teach her (e.g., 'Store', 'Lobby'), or type 'done' to exit:\n> ").strip().lower()

        if screen_name == 'done':
            break
        if not screen_name:
            continue

        clear_screen()
        print(f"\nPlease go to the '{screen_name.capitalize()}' screen in Valorant.")
        print(f"When you are ready, press '{CAPTURE_KEY}' to capture the screen.")

        # Wait for the hotkey
        keyboard.wait(CAPTURE_KEY)
        print("\nScreenshot captured!")

        # Give a moment for the key press to not interfere with the screenshot
        time.sleep(0.5)

        full_screenshot = perception.capture_screen()
        if full_screenshot is None:
            print("[ERROR] Could not capture the screen. Please try again.")
            continue

        # Let the user select the unique part of the screen
        x, y, w, h = select_roi(full_screenshot)

        if w == 0 or h == 0:
            print("[WARNING] You did not select a region. Please try again.")
            continue

        template_image = full_screenshot[y:y+h, x:x+w]

        # Save the template
        template_path = os.path.join(TEMPLATES_DIR, f"{screen_name}.png")
        cv2.imwrite(template_path, template_image)

        print(f"\n[SUCCESS] I have learned what the '{screen_name.capitalize()}' screen looks like.")
        print(f"Template saved to: {template_path}")

    clear_screen()
    print("--- Teaching Complete ---")
    print("Thank you for teaching me! I can now use this knowledge to be more aware.")
    print("You can run this script again at any time to teach me more screens.")


if __name__ == "__main__":
    run_teaching_wizard()