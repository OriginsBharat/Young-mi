# src/screen_perception.py

import psutil
import mss
import numpy as np
import cv2
import pytesseract
from PIL import Image

class ScreenPerception:
    def __init__(self, valorant_process_name="VALORANT.exe"):
        self.valorant_process_name = valorant_process_name
        self.sct = mss.mss()
        # Optional: If Tesseract is not in your PATH, you might need to set this.
        # Example for Windows:
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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
            # Convert to a format that OpenCV can use (numpy array)
            img = np.array(sct_img)
            # Convert from BGRA to BGR
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

        # Pre-process the image for better OCR results
        gray_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        # Apply thresholding to get a binary image
        _, thresh_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        try:
            text = pytesseract.image_to_string(thresh_img, config='--psm 6')
            return text.strip()
        except pytesseract.TesseractNotFoundError:
            print("[ERROR] Tesseract not found. Please install it and ensure it's in your system's PATH.")
            return None
        except Exception as e:
            print(f"An error occurred during OCR: {e}")
            return None

    def find_template_on_screen(self, screen_image, template_path, threshold=0.8):
        """
        Finds if a given template image is present on the screen.
        Returns the coordinates of the match or None.
        """
        if screen_image is None:
            return None

        try:
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                raise FileNotFoundError(f"Template image not found at {template_path}")

            w, h = template.shape[::-1]
        except Exception as e:
            print(f"Error loading template: {e}")
            return None

        screen_gray = cv2.cvtColor(screen_image, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)

        # Return the top-left coordinate of the first match
        for pt in zip(*loc[::-1]):
            return pt
        return None

if __name__ == '__main__':
    # This block is for testing the module directly
    print("Testing Screen Perception module...")
    perception = ScreenPerception()

    print("\nChecking if Valorant is running...")
    if perception.is_valorant_running():
        print("   Valorant process found!")

        print("\nAttempting to take a screenshot in 3 seconds...")
        import time
        time.sleep(3)
        screenshot = perception.capture_screen()

        if screenshot is not None:
            cv2.imwrite("test_screenshot.jpg", screenshot)
            print("   Screenshot saved as test_screenshot.jpg")

            # Note: OCR and template matching are highly dependent on screen resolution
            # and having the game open. These are placeholder examples.
            print("\nTesting OCR on a sample region (top-left corner)...")
            # Define a small region at the top-left to test OCR
            test_roi = (0, 0, 300, 100)
            ocr_text = perception.ocr_region(screenshot, test_roi)
            print(f"   OCR Result: '{ocr_text}'")

            print("\nTesting template matching (requires 'test_template.png')...")
            # For this test to work, you'd need a file named 'test_template.png'
            # that is a small snippet of the current screen.
            if not os.path.exists('test_template.png'):
                # Create a dummy template from the screenshot for testing purposes
                dummy_template = screenshot[50:100, 50:100]
                cv2.imwrite('test_template.png', dummy_template)
                print("   Created a dummy 'test_template.png' for testing.")

            match_location = perception.find_template_on_screen(screenshot, 'test_template.png')
            if match_location:
                print(f"   Template found at coordinates: {match_location}")
            else:
                print("   Template not found.")

    else:
        print("   Valorant is not running. Live tests will be skipped.")