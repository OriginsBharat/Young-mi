import cv2
import numpy as np
import mss
import pytesseract
import os
import time

# --- Configuration ---
# ROIs (Regions of Interest) for different UI elements.
# You will likely need to adjust these for your specific screen resolution.
# A good way to find these coordinates is to take a screenshot and use an image editor.
# TODO: Make these configurable from a JSON file.
NAV_BAR_ROI = (400, 0, 1120, 80)      # Top-center of the screen for the main navigation tabs
KILL_FEED_ROI = (1500, 200, 400, 200)  # Top-right area for the kill feed
ROUND_END_ROI = (760, 200, 400, 200)   # Center of the screen for VICTORY/DEFEAT

# The username of the player. IMPORTANT: This MUST be set to your exact Valorant username.
PLAYER_USERNAME = "YourValorantName"

def capture_screen_area(roi):
    """Captures a specific region of the primary monitor."""
    with mss.mss() as sct:
        monitor = {"top": roi[1], "left": roi[0], "width": roi[2], "height": roi[3]}
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

def preprocess_image_for_ocr(image, invert=True):
    """Applies preprocessing steps to an image to improve OCR accuracy."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if invert:
        # Inverting the colors can help with light text on a dark background.
        gray = cv2.bitwise_not(gray)

    # Thresholding to get a clean, binary image.
    _, binary_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return binary_image

def read_text_from_image(image, psm=7):
    """Performs OCR on a given image and returns the extracted text."""
    try:
        # --psm 7 treats the image as a single text line, which is good for the nav bar.
        custom_config = f'--oem 3 --psm {psm}'
        text = pytesseract.image_to_string(image, config=custom_config)
        return text.strip().upper()
    except pytesseract.TesseractNotFoundError:
        print("ERROR: Tesseract is not installed or not in your PATH.")
        return ""
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return ""

def get_current_screen():
    """
    Determines the current active screen in Valorant by reading the navigation bar.
    Returns a string representing the current screen (e.g., "HOME", "STORE", "UNKNOWN").
    """
    img = capture_screen_area(NAV_BAR_ROI)
    processed_img = preprocess_image_for_ocr(img, invert=False) # Nav bar text is often on a lighter background
    text = read_text_from_image(processed_img, psm=7)

    # Check for keywords that indicate the current screen
    if "PLAY" in text: return "HOME"
    if "BATTLEPASS" in text: return "BATTLEPASS"
    if "AGENTS" in text: return "AGENTS"
    if "CAREER" in text: return "CAREER"
    if "COLLECTION" in text: return "COLLECTION"
    if "STORE" in text: return "STORE"

    # If we're not in a main menu, we might be in a match or loading screen
    # For now, we'll label this as IN_MATCH, but this can be refined
    return "IN_MATCH" # Default state if no tabs are detected

def check_for_kill():
    """Checks the kill feed to see if the player got a kill."""
    img = capture_screen_area(KILL_FEED_ROI)
    processed_img = preprocess_image_for_ocr(img)
    text = read_text_from_image(processed_img, psm=6)
    lines = text.split('\n')
    for line in lines:
        if line.strip().startswith(PLAYER_USERNAME):
            return True
    return False

def check_for_death():
    """Checks the kill feed to see if the player died."""
    img = capture_screen_area(KILL_FEED_ROI)
    processed_img = preprocess_image_for_ocr(img)
    text = read_text_from_image(processed_img, psm=6)
    lines = text.split('\n')
    for line in lines:
        if (' ' + PLAYER_USERNAME) in line.strip() and not line.strip().startswith(PLAYER_USERNAME):
             return True
    return False

def check_round_end():
    """Checks for round end banners (VICTORY or DEFEAT)."""
    img = capture_screen_area(ROUND_END_ROI)
    processed_img = preprocess_image_for_ocr(img, invert=False)
    text = read_text_from_image(processed_img).upper()
    if "VICTORY" in text: return "VICTORY"
    if "DEFEAT" in text: return "DEFEAT"
    return None

if __name__ == '__main__':
    print("--- Testing game_awareness.py (V2 Vision) ---")
    print(f"Watching for player: '{PLAYER_USERNAME}'. Make sure this is correct.")
    print("Press Ctrl+C to stop.")

    last_screen = ""
    while True:
        try:
            current_screen = get_current_screen()
            if current_screen != last_screen:
                print(f">>> Game State Changed: Now on screen '{current_screen}'")
                last_screen = current_screen

            if current_screen == "IN_MATCH":
                if check_for_kill():
                    print(">>> Event Detected: PLAYER_KILL")
                if check_for_death():
                    print(">>> Event Detected: PLAYER_DEATH")
                round_status = check_round_end()
                if round_status:
                    print(f">>> Event Detected: ROUND_END ({round_status})")

            time.sleep(2)
        except KeyboardInterrupt:
            print("\nStopping test.")
            break
        except Exception as e:
            print(f"An error occurred in the test loop: {e}")
            break