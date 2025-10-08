# src/screen_perception.py

import psutil
import mss
import numpy as np
import cv2
import pytesseract
import os

class ScreenPerception:
    def __init__(self, valorant_process_name="VALORANT.exe"):
        self.valorant_process_name = valorant_process_name
        self.sct = mss.mss()

    def is_valorant_running(self):
        """Checks if the Valorant process is currently running."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == self.valorant_process_name:
                return True
        return False

    def capture_screen(self, monitor_number=1):
        """
        Captures the screen of the specified monitor.
        Returns a CV2 image (in BGR format).
        """
        try:
            monitor = self.sct.monitors[monitor_number]
            sct_img = self.sct.grab(monitor)
            img = np.array(sct_img)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except mss.exception.ScreenShotError as e:
            print(f"Error capturing screen: {e}")
            return None

    def ocr_region(self, screen_image, region):
        """
        Performs OCR on a specified region of a captured image.
        `region` should be a tuple: (x, y, width, height).
        """
        if screen_image is None:
            return None

        x, y, w, h = region
        crop_img = screen_image[y:y+h, x:x+w]

        # Pre-process for better OCR results
        gray_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        thresh_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        try:
            text = pytesseract.image_to_string(thresh_img, config='--psm 6')
            return text.strip()
        except Exception as e:
            print(f"An error occurred during OCR: {e}")
            return None

    def find_template_on_screen(self, screen_image, template_path, threshold=0.8):
        """Finds if a given template image is present on the screen."""
        if screen_image is None:
            return None

        try:
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                # This is not an error, it just means the template doesn't exist yet.
                return None

            w, h = template.shape[::-1]
        except Exception as e:
            print(f"Error loading template: {e}")
            return None

        screen_gray = cv2.cvtColor(screen_image, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        if max_val >= threshold:
            return True
        return False

    def find_all_templates_on_screen(self, screen_image, templates_dir="data/templates"):
        """Iterates through all templates and returns the name of the first one found."""
        if not os.path.exists(templates_dir):
            return "Unknown"

        for template_file in os.listdir(templates_dir):
            if template_file.endswith(".png"):
                template_path = os.path.join(templates_dir, template_file)
                if self.find_template_on_screen(screen_image, template_path):
                    # Return the name of the screen, which is the filename without the extension.
                    return os.path.splitext(template_file)[0]

        return "Unknown"