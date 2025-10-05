import cv2
import numpy as np
import mss
import pytesseract
import os
import time

# --- Configuration ---
# You will need to define the screen regions for different game events.
# These are (x, y, width, height) tuples.
# You'll likely need to adjust these for your specific screen resolution.
# A good way to find these coordinates is to take a screenshot and use an image editor.
# TODO: Make these configurable, perhaps from a JSON file.
KILL_FEED_ROI = (1500, 200, 400, 200)  # Top-right area for the kill feed
ROUND_END_ROI = (760, 200, 400, 200)   # Center of the screen for VICTORY/DEFEAT

# The username of the player, so the AI knows who to look for in the kill feed.
# IMPORTANT: This MUST be set to your exact Valorant username for kill/death detection to work.
PLAYER_USERNAME = "YourValorantName"

# --- Template for Lobby Detection ---
# We still use simple template matching for lobby detection as it's reliable.
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'templates')

def capture_screen_area(roi):
    """
    Captures a specific region of the primary monitor.
    - roi: A tuple (x, y, width, height) defining the region of interest.
    Returns the captured region as an OpenCV image.
    """
    with mss.mss() as sct:
        monitor = {"top": roi[1], "left": roi[0], "width": roi[2], "height": roi[3]}
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

def preprocess_image_for_ocr(image):
    """
    Applies preprocessing steps to an image to improve OCR accuracy.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Using a threshold to create a clean binary image. This is crucial for OCR.
    _, binary_image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary_image

def read_text_from_image(image):
    """
    Performs OCR on a given image and returns the extracted text.
    """
    try:
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, config=custom_config)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        print("ERROR: Tesseract is not installed or not in your PATH.")
        return ""
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return ""

def check_for_kill():
    """
    Checks the kill feed to see if the player got a kill.
    Returns True if a kill is detected, False otherwise.
    """
    img = capture_screen_area(KILL_FEED_ROI)
    processed_img = preprocess_image_for_ocr(img)
    text = read_text_from_image(processed_img)

    # A kill is when a line in the feed STARTS with the player's name.
    lines = text.split('\n')
    for line in lines:
        if line.strip().startswith(PLAYER_USERNAME):
            return True
    return False

def check_for_death():
    """
    Checks the kill feed to see if the player died.
    Returns True if a death is detected, False otherwise.
    """
    img = capture_screen_area(KILL_FEED_ROI)
    processed_img = preprocess_image_for_ocr(img)
    text = read_text_from_image(processed_img)

    # A death is when a line in the feed ENDS with the player's name.
    lines = text.split('\n')
    for line in lines:
        # Check for ' ' + PLAYER_USERNAME to avoid matching partial names (e.g., "Player" in "OtherPlayer")
        if (' ' + PLAYER_USERNAME) in line.strip() and not line.strip().startswith(PLAYER_USERNAME):
             return True
    return False

def check_round_end():
    """
    Checks for round end banners (VICTORY or DEFEAT).
    Returns "VICTORY", "DEFEAT", or None.
    """
    img = capture_screen_area(ROUND_END_ROI)
    # For round end banners, we don't need as much preprocessing
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = read_text_from_image(gray_img).upper()

    if "VICTORY" in text:
        return "VICTORY"
    if "DEFEAT" in text:
        return "DEFEAT"

    return None

def is_valorant_lobby_open():
    """
    Checks if the Valorant lobby is open using template matching.
    """
    template_path = os.path.join(TEMPLATE_DIR, "valorant_lobby_template.png")
    if not os.path.exists(template_path):
        return False

    with mss.mss() as sct:
        screen = np.array(sct.grab(sct.monitors[1]))
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None: return False

    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)

    return max_val > 0.8


if __name__ == '__main__':
    print("--- Testing game_awareness.py (Advanced OCR Version) ---")
    print(f"Watching for player: '{PLAYER_USERNAME}'. IMPORTANT: Make sure this is your exact in-game name.")
    print("Press Ctrl+C to stop.")

    while True:
        try:
            if check_for_kill():
                print(">>> Event Detected: PLAYER_KILL")
            if check_for_death():
                print(">>> Event Detected: PLAYER_DEATH")
            round_status = check_round_end()
            if round_status:
                print(f">>> Event Detected: ROUND_END ({round_status})")
            if is_valorant_lobby_open():
                print(">>> Event Detected: LOBBY_OPEN")

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping test.")
            break
        except Exception as e:
            print(f"An error occurred in the test loop: {e}")
            break