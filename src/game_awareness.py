import cv2
import numpy as np
import mss
import pytesseract
import os
from dotenv import load_dotenv

# Load environment variables to get the player's username
load_dotenv()

# --- Configuration ---
# ROIs (Regions of Interest) for different UI elements.
NAV_BAR_ROI = (400, 0, 1120, 80)
KILL_FEED_ROI = (1500, 200, 400, 200)
ROUND_END_ROI = (760, 200, 400, 200)
AGENT_SELECT_ROI = (860, 800, 200, 100)
SCORE_ROI = (900, 10, 120, 40)
PLAYERS_ALIVE_ROI = (850, 80, 220, 40)

PLAYER_USERNAME = os.getenv("PLAYER_USERNAME", "YourValorantName")
ABILITY_ICON_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'ability_icons')
os.makedirs(ABILITY_ICON_DIR, exist_ok=True)

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

def read_text_from_image(image, psm=7, is_numeric=False):
    """Performs OCR on a given image and returns the extracted text."""
    try:
        config = f'--oem 3 --psm {psm}'
        if is_numeric:
            config += ' -c tessedit_char_whitelist=0123456789-'
        text = pytesseract.image_to_string(image, config=config)
        return text.strip().upper()
    except Exception as e:
        print(f"[ERROR] An error occurred during OCR: {e}")
        return ""

def get_current_game_context():
    """Reads multiple parts of the HUD to get a full tactical overview."""
    score_img = capture_screen_area(SCORE_ROI)
    players_img = capture_screen_area(PLAYERS_ALIVE_ROI)

    score_processed = preprocess_image_for_ocr(score_img, invert=False)
    players_processed = preprocess_image_for_ocr(players_img, invert=False)

    score_text = read_text_from_image(score_processed, is_numeric=True)
    players_text = read_text_from_image(players_processed, is_numeric=True)

    score = score_text.replace(" ", "").replace("\n", "")
    players_alive = players_text.replace(" ", "").replace("\n", "").replace("|", "v")

    return {"score": score, "players_alive": players_alive}

def is_agent_select_screen():
    img = capture_screen_area(AGENT_SELECT_ROI)
    processed_img = preprocess_image_for_ocr(img, invert=False)
    text = read_text_from_image(processed_img, psm=7)
    return "LOCK IN" in text

def get_current_screen():
    if is_agent_select_screen(): return "AGENT_SELECT"
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
    img = capture_screen_area(KILL_FEED_ROI)
    processed_img = preprocess_image_for_ocr(img)
    text = read_text_from_image(processed_img, psm=6)
    for line in text.split('\n'):
        if line.strip().startswith(PLAYER_USERNAME): return True
    return False

def check_for_death():
    img = capture_screen_area(KILL_FEED_ROI)
    processed_img = preprocess_image_for_ocr(img)
    text = read_text_from_image(processed_img, psm=6)
    for line in text.split('\n'):
        if (' ' + PLAYER_USERNAME) in line.strip() and not line.strip().startswith(PLAYER_USERNAME): return True
    return False

def check_round_end():
    img = capture_screen_area(ROUND_END_ROI)
    processed_img = preprocess_image_for_ocr(img, invert=False)
    text = read_text_from_image(processed_img)
    if "VICTORY" in text: return "VICTORY"
    if "DEFEAT" in text: return "DEFEAT"
    return None

def detect_agents_in_match():
    print("[INFO] Placeholder: Detecting agents in match...")
    return ["jett", "sova", "viper", "reyna", "killjoy", "cypher", "sage", "omen", "breach", "phoenix"]

def check_for_ability_use():
    kill_feed_img = capture_screen_area(KILL_FEED_ROI)
    kill_feed_gray = cv2.cvtColor(kill_feed_img, cv2.COLOR_BGR2GRAY)
    for icon_file in os.listdir(ABILITY_ICON_DIR):
        if icon_file.endswith(".png"):
            template_path = os.path.join(ABILITY_ICON_DIR, icon_file)
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None: continue
            res = cv2.matchTemplate(kill_feed_gray, template, cv2.TM_CCOEFF_NORMED)
            if cv2.minMaxLoc(res)[1] > 0.85: return os.path.splitext(icon_file)[0]
    return None

def get_all_text_on_screen():
    """Captures the full screen and extracts all text for autonomous learning."""
    with mss.mss() as sct:
        sct_img = sct.grab(sct.monitors[1])
        img = np.array(sct_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    return read_text_from_image(binary_image, psm=3)

if __name__ == '__main__':
    print("--- Testing game_awareness.py (Definitive Version) ---")
    while True:
        try:
            current_screen = get_current_screen()
            print(f"Current Screen: {current_screen}")
            if current_screen == "IN_MATCH":
                context = get_current_game_context()
                print(f"  -> Game Context: Score {context['score']}, Players {context['players_alive']}")
            time.sleep(2)
        except KeyboardInterrupt:
            break