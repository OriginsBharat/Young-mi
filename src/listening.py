import speech_recognition as sr

# This module handles capturing and transcribing audio from the microphone.

def listen_for_command():
    """
    Listens for a command from the user via the microphone and returns the transcribed text.
    Returns None if no speech is detected or if there's an error.
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        # A short adjustment for ambient noise to improve responsiveness.
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("[INFO] Listening for voice command...")

        try:
            # Listen for speech with a timeout to avoid blocking forever.
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            print("[INFO] Recognizing speech...")

            # Use Google's free web speech API for transcription.
            text = recognizer.recognize_google(audio)
            print(f"[INFO] Heard: '{text}'")
            return text

        except sr.WaitTimeoutError:
            # This is not an error, just a timeout. Return None.
            return None
        except sr.UnknownValueError:
            print("[ERROR] Could not understand the audio.")
            return None
        except sr.RequestError as e:
            print(f"[ERROR] Could not request results from Google Web Speech API; {e}")
            return None
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred during listening: {e}")
            return None

if __name__ == '__main__':
    print("--- Testing listening.py ---")
    print("Say something, and I will try to recognize it.")
    print("Say 'stop listening' to end the test.")

    while True:
        command = listen_for_command()
        if command:
            print(f"Recognized: '{command}'")
            if "stop listening" in command.lower():
                print("Stopping test.")
                break
        else:
            # If nothing is heard, just loop again.
            pass