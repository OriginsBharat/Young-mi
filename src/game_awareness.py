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
AGENT_SELECT_ROI = (860, 800, 200, 100) # Bottom-center of the screen for the "LOCK IN" button

# The username of the player is now loaded from the environment variables.
PLAYER_USERNAME = os.getenv("PLAYER_USERNAME", "YourValorantName")

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

def is_agent_select_screen():
    """
    Checks if the user is on the Agent Select screen by looking for the 'LOCK IN' button.
    """
    img = capture_screen_area(AGENT_SELECT_ROI)
    # The "LOCK IN" button has white text, so we don't need to invert.
    processed_img = preprocess_image_for_ocr(img, invert=False)
    text = read_text_from_image(processed_img, psm=7).upper()

    return "LOCK IN" in text

def get_current_screen():
    """
    Determines the current active screen in Valorant by reading the navigation bar.
    Returns a string representing the current screen (e.g., "HOME", "STORE", "UNKNOWN").
    """
    # Agent select is a special case that doesn't have the top nav bar, so check for it first.
    if is_agent_select_screen():
        return "AGENT_SELECT"

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

def detect_agents_in_match():
    """
    Placeholder function to detect the agents in the current match.
    In a future version, this would use computer vision on the agent select screen
    or the in-game scoreboard.
    For now, it returns a fixed list for testing purposes.
    """
    # TODO: Implement actual agent detection using OCR or template matching on the scoreboard.
    print("Placeholder: Detecting agents in match...")
    return ["jett", "sova", "viper", "reyna", "killjoy", "cypher", "sage", "omen", "breach", "phoenix"]

def check_for_ability_use():
    """
    Checks the kill feed area for known ability icons.
    Returns the name of the detected ability (from the image filename) or None.
    """
    ability_icon_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'ability_icons')
    if not os.path.exists(ability_icon_dir):
        return None

    kill_feed_img = capture_screen_area(KILL_FEED_ROI)
    kill_feed_gray = cv2.cvtColor(kill_feed_img, cv2.COLOR_BGR2GRAY)

    # Iterate over all the icon templates the user has taught her
    for icon_file in os.listdir(ability_icon_dir):
        if icon_file.endswith(".png"):
            template_path = os.path.join(ability_icon_dir, icon_file)
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

            if template is None: continue

            res = cv2.matchTemplate(kill_feed_gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)

            # If we find a strong match, return the name of the ability
            if max_val > 0.85: # Using a slightly higher threshold for icons
                ability_name = os.path.splitext(icon_file)[0]
                # print(f"Detected ability use: {ability_name}")
                return ability_name

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