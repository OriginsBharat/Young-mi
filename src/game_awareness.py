import cv2
import numpy as np
import mss
import pytesseract
import os
import time
from dotenv import load_dotenv

# Load environment variables to get the player's username
load_dotenv()

# --- Configuration ---
# ROIs (Regions of Interest) for different UI elements.
NAV_BAR_ROI = (400, 0, 1120, 80)
KILL_FEED_ROI = (1500, 200, 400, 200)
ROUND_END_ROI = (760, 200, 400, 200)
AGENT_SELECT_ROI = (860, 800, 200, 100)

PLAYER_USERNAME = os.getenv("PLAYER_USERNAME", "YourValorantName")
ABILITY_ICON_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'ability_icons')
os.makedirs(ABILITY_ICON_DIR, exist_ok=True) # Ensure the directory exists

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
        gray = cv2.bitwise_not(gray)
    _, binary_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return binary_image

def read_text_from_image(image, psm=7):
    """Performs OCR on a given image and returns the extracted text."""
    try:
        custom_config = f'--oem 3 --psm {psm}'
        text = pytesseract.image_to_string(image, config=custom_config)
        return text.strip().upper()
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return ""

def is_agent_select_screen():
    """Checks if the user is on the Agent Select screen by looking for the 'LOCK IN' button."""
    img = capture_screen_area(AGENT_SELECT_ROI)
    processed_img = preprocess_image_for_ocr(img, invert=False)
    text = read_text_from_image(processed_img, psm=7)
    return "LOCK IN" in text

def get_current_screen():
    """Determines the current active screen in Valorant."""
    if is_agent_select_screen():
        return "AGENT_SELECT"

    img = capture_screen_area(NAV_BAR_ROI)
    processed_img = preprocess_image_for_ocr(img, invert=False)
    text = read_text_from_image(processed_img, psm=7)

    if "PLAY" in text: return "HOME"
    if "BATTLEPASS" in text: return "BATTLEPASS"
    if "AGENTS" in text: return "AGENTS"
    if "CAREER" in text: return "CAREER"
    if "COLLECTION" in text: return "COLLECTION"
    if "STORE" in text: return "STORE"

    return "IN_MATCH"

def check_for_kill():
    """Checks the kill feed to see if the player got a kill."""
    img = capture_screen_area(KILL_FEED_ROI)
    processed_img = preprocess_image_for_ocr(img)
    text = read_text_from_image(processed_img, psm=6)
    for line in text.split('\n'):
        if line.strip().startswith(PLAYER_USERNAME):
            return True
    return False

def check_for_death():
    """Checks the kill feed to see if the player died."""
    img = capture_screen_area(KILL_FEED_ROI)
    processed_img = preprocess_image_for_ocr(img)
    text = read_text_from_image(processed_img, psm=6)
    for line in text.split('\n'):
        if (' ' + PLAYER_USERNAME) in line.strip() and not line.strip().startswith(PLAYER_USERNAME):
             return True
    return False

def check_round_end():
    """Checks for round end banners."""
    img = capture_screen_area(ROUND_END_ROI)
    processed_img = preprocess_image_for_ocr(img, invert=False)
    text = read_text_from_image(processed_img)
    if "VICTORY" in text: return "VICTORY"
    if "DEFEAT" in text: return "DEFEAT"
    return None

def detect_agents_in_match():
    """Placeholder function to detect agents in a match."""
    print("Placeholder: Detecting agents in match...")
    return ["jett", "sova", "viper", "reyna", "killjoy", "cypher", "sage", "omen", "breach", "phoenix"]

def check_for_ability_use():
    """Checks the kill feed area for known ability icons."""
    kill_feed_img = capture_screen_area(KILL_FEED_ROI)
    kill_feed_gray = cv2.cvtColor(kill_feed_img, cv2.COLOR_BGR2GRAY)

    for icon_file in os.listdir(ABILITY_ICON_DIR):
        if icon_file.endswith(".png"):
            template_path = os.path.join(ABILITY_ICON_DIR, icon_file)
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None: continue

            res = cv2.matchTemplate(kill_feed_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val > 0.85:
                return os.path.splitext(icon_file)[0]
    return None

if __name__ == '__main__':
    print("--- Testing game_awareness.py ---")
    while True:
        try:
            current_screen = get_current_screen()
            print(f"Current Screen: {current_screen}")
            if current_screen == "IN_MATCH":
                if check_for_kill(): print(">>> Event: PLAYER_KILL")
                if check_for_death(): print(">>> Event: PLAYER_DEATH")
                round_status = check_round_end()
                if round_status: print(f">>> Event: ROUND_END ({round_status})")
            time.sleep(2)
        except KeyboardInterrupt:
            break