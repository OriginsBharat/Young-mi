import os
import time
import mss
import cv2
import numpy as np
from pynput import keyboard

# --- Configuration ---
# The hotkey combination to trigger a screenshot.
# You can change this if you like.
HOTKEY = {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.KeyCode.from_char('t')}

# The directory where the training data will be saved.
TRAINING_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'training_data')

# A set to keep track of currently pressed keys.
current_keys = set()

def capture_and_save_screenshot():
    """
    Captures the screen, asks the user for a label, and saves the image.
    """
    print("\n--- Hotkey Activated! ---")

    # 1. Capture the screen
    with mss.mss() as sct:
        sct_img = sct.grab(sct.monitors[1]) # Capture the primary monitor
        img = np.array(sct_img)
        # Convert to a standard format (BGR) for saving with OpenCV
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    print("Screenshot captured.")

    # 2. Ask the user for a label
    try:
        label = input("What screen is this? Please provide a descriptive name (e.g., 'jett_contract_screen'): ")
        if not label:
            print("No label provided. Aborting save.")
            return

        # Sanitize the label to make it a valid filename
        filename = "".join(c for c in label if c.isalnum() or c in ('_', '-')).rstrip()
        filename = f"{filename}_{int(time.time())}.png"

        # 3. Save the image
        save_path = os.path.join(TRAINING_DATA_DIR, filename)
        cv2.imwrite(save_path, img)

        print(f"Successfully saved training image as: {save_path}")
        print("You can press the hotkey again to teach her something new.")

    except Exception as e:
        print(f"An error occurred while saving the screenshot: {e}")


def on_press(key):
    """Callback function for when a key is pressed."""
    if key in HOTKEY:
        current_keys.add(key)
        if all(k in current_keys for k in HOTKEY):
            capture_and_save_screenshot()

def on_release(key):
    """Callback function for when a key is released."""
    try:
        current_keys.remove(key)
    except KeyError:
        pass

def main():
    """Main function to start the hotkey listener."""
    print("--- Kim Young-mi: Teaching Mode ---")
    print(f"Press the hotkey ({' + '.join(str(k) for k in HOTKEY)}) to capture a screen.")
    print("Navigate to any screen in Valorant you want her to learn.")
    print("Press Ctrl+C in this terminal to stop the teaching mode.")

    # Start listening for keyboard events
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            print("\nStopping Teaching Mode. Goodbye.")

if __name__ == "__main__":
    main()