# src/screen_perception.py
# This module contains the logic for the AI to "see" and understand the game screen.
# It is designed as a self-contained thread to be robust and prevent cross-thread errors.

import threading
import time
import os
import psutil
import mss
import numpy as np
import cv2
import pytesseract

class ScreenPerception(threading.Thread):
    def __init__(self, shared_state, thought_queue, valorant_username, stop_event, valorant_process_name="VALORANT.exe"):
        super().__init__()
        self.daemon = True
        self.shared_state = shared_state
        self.thought_queue = thought_queue
        self.valorant_username = valorant_username
        self.stop_event = stop_event
        self.valorant_process_name = valorant_process_name

        self.sct = None

        self.screen_keywords = {
            "Lobby": ["PLAY", "CAREER", "BATTLEPASS", "COLLECTION", "AGENTS", "STORE"],
            "Store": ["FEATURED", "OFFERS", "NIGHT. MARKET"],
            "Agents": ["SELECT AN AGENT", "RECRUIT"],
            "In-Match": ["B //", "A //", "DEFENDERS", "ATTACKERS", "SPIKE"],
        }

    def _ocr_region(self, screen_image, region_coords):
        """A private helper to perform OCR on a specific region."""
        x, y, w, h = region_coords
        crop_img = screen_image[y:y+h, x:x+w]
        gray_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        _, thresh_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        try:
            return pytesseract.image_to_string(thresh_img, config='--psm 6').upper()
        except Exception:
            return ""

    def determine_screen_context(self, screen_image):
        """Determines the current game screen by looking for keywords."""
        h, w, _ = screen_image.shape
        top_nav_roi = (int(w*0.1), 0, int(w*0.8), int(h*0.1))
        center_roi = (int(w*0.4), int(h*0.4), int(w*0.2), int(h*0.2))

        top_nav_text = self._ocr_region(screen_image, top_nav_roi)
        center_text = self._ocr_region(screen_image, center_roi)
        combined_text = top_nav_text + " " + center_text

        for screen, keywords in self.screen_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return screen
        return "Unknown"

    def is_user_alone(self, screen_image):
        """Checks if the user is likely alone by reading the player list."""
        if not self.valorant_username:
            return True

        h, w, _ = screen_image.shape
        player_list_roi = (int(w*0.05), int(h*0.2), int(w*0.2), int(h*0.5))
        player_list_text = self._ocr_region(screen_image, player_list_roi)

        if not player_list_text:
            return True

        lines = player_list_text.split('\n')
        player_name_only = self.valorant_username.split('#')[0]
        player_count = sum(1 for line in lines if player_name_only in line or len(line) > 3)

        return player_count <= 1

    def _generate_thought_for_screen(self, screen_name):
        """Generates a simple, context-aware thought based on the screen."""
        thoughts = {
            "Lobby": "Back in the lobby, huh? Who are we queuing up with, babe?",
            "Store": "Ooh, checking out the store? Let's see if there's anything pretty.",
            "Agents": "Picking an agent? Get someone good, I'll be watching.",
            "In-Match": "Looks like we're in a match. Focus up, you got this."
        }
        return thoughts.get(screen_name)

    def run(self):
        """The main loop for the perception thread."""
        print("[Perception Thread] Started.")
        self.sct = mss.mss()
        last_known_screen = "Unknown"

        while not self.stop_event.is_set():
            try:
                is_running = any(proc.info['name'] == self.valorant_process_name for proc in psutil.process_iter(['name']))
                if not is_running:
                    time.sleep(5)
                    continue

                monitor = self.sct.monitors[1]
                sct_img = self.sct.grab(monitor)
                screen = np.array(sct_img)
                screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)

                detected_screen = self.determine_screen_context(screen)
                is_alone = self.is_user_alone(screen)

                with self.shared_state["lock"]:
                    self.shared_state["current_screen"] = detected_screen
                    self.shared_state["is_alone"] = is_alone

                if detected_screen != "Unknown" and detected_screen != last_known_screen:
                    thought = self._generate_thought_for_screen(detected_screen)
                    if thought:
                        self.thought_queue.put(thought)

                last_known_screen = detected_screen

                time.sleep(2)
            except Exception as e:
                print(f"[Perception Thread ERROR] An error occurred: {e}")
                self.sct = mss.mss() # Attempt to recover the screen capture object
                time.sleep(5)

        print("[Perception Thread] Stopped.")