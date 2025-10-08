# src/screen_perception.py
# This module contains the logic for the AI to "see" and understand the game screen.

import psutil
import mss
import numpy as np
import cv2
import pytesseract

class ScreenPerception:
    def __init__(self, valorant_process_name="VALORANT.exe"):
        self.valorant_process_name = valorant_process_name
        self.sct = mss.mss()

        # Define keywords for each screen. This makes the system modular and easy to expand.
        self.screen_keywords = {
            "Lobby": ["PLAY", "CAREER", "BATTLEPASS", "COLLECTION", "AGENTS", "STORE"],
            "Store": ["FEATURED", "OFFERS", "NIGHT. MARKET"],
            "Agents": ["SELECT AN AGENT", "RECRUIT"],
            "In-Match": ["B //", "A //", "DEFENDERS", "ATTACKERS"], # Keywords likely to appear only in a match
        }

    def is_valorant_running(self):
        """Checks if the Valorant process is currently running."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == self.valorant_process_name:
                return True
        return False

    def capture_screen(self, monitor_number=1):
        """Captures the screen of the specified monitor and returns a CV2 image."""
        try:
            monitor = self.sct.monitors[monitor_number]
            sct_img = self.sct.grab(monitor)
            img = np.array(sct_img)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except mss.exception.ScreenShotError as e:
            print(f"Error capturing screen: {e}")
            return None

    def _ocr_region(self, screen_image, region_coords):
        """A private helper to perform OCR on a specific region."""
        if screen_image is None:
            return ""
        x, y, w, h = region_coords
        crop_img = screen_image[y:y+h, x:x+w]
        gray_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        # Apply thresholding to make text more distinct
        _, thresh_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        try:
            return pytesseract.image_to_string(thresh_img, config='--psm 6').upper()
        except Exception:
            return ""

    def determine_screen_context(self, screen_image):
        """
        Determines the current game screen by looking for keywords in specific regions.
        This is resolution-independent as it uses percentages.
        """
        if screen_image is None:
            return "Unknown"

        h, w, _ = screen_image.shape

        # Define ROIs using percentages for resolution independence
        # Top navigation bar (for Lobby, Store, etc.)
        top_nav_roi = (int(w*0.1), 0, int(w*0.8), int(h*0.1))
        # Center of screen (for in-match HUD elements)
        center_roi = (int(w*0.4), int(h*0.4), int(w*0.2), int(h*0.2))

        # Perform OCR on the defined regions
        top_nav_text = self._ocr_region(screen_image, top_nav_roi)
        center_text = self._ocr_region(screen_image, center_roi)

        combined_text = top_nav_text + " " + center_text

        # Check for keywords
        for screen, keywords in self.screen_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return screen

        return "Unknown"

    def is_user_alone(self, screen_image, username):
        """
        Checks if the user is likely alone by reading the player list.
        A simple heuristic for now.
        """
        if screen_image is None or not username:
            return True # Default to being alone if we can't check

        h, w, _ = screen_image.shape
        # A plausible region for the player list in the lobby
        player_list_roi = (int(w*0.05), int(h*0.2), int(w*0.2), int(h*0.5))

        player_list_text = self._ocr_region(screen_image, player_list_roi)

        # If we can't read any text, assume alone to be safe
        if not player_list_text:
            return True

        # If we find more than one name-like line, assume not alone.
        # This is a very basic check and can be improved.
        lines = player_list_text.split('\n')
        player_count = sum(1 for line in lines if '#' in line or len(line) > 3) # Count lines that look like player names

        return player_count <= 1

if __name__ == '__main__':
    # This test will fail in a headless environment, but it serves to validate the code structure.
    print("--- Testing Automated Screen Perception Engine ---")
    perception = ScreenPerception()
    print("Class initialized successfully.")
    print(f"Defined screen keywords: {perception.screen_keywords}")

    # The following calls will fail because there is no screen to capture.
    print("\nAttempting to call perception functions (will fail in headless environment)...")
    try:
        mock_screen = np.zeros((1080, 1920, 3), dtype=np.uint8)
        context = perception.determine_screen_context(mock_screen)
        print(f"  determine_screen_context call successful. Result: {context}")
        alone = perception.is_user_alone(mock_screen, "TestUser#123")
        print(f"  is_user_alone call successful. Result: {alone}")
    except Exception as e:
        print(f"  Correctly failed in headless environment: {e}")
    print("\n--- Test Complete ---")