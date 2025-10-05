import speech_recognition as sr

def listen_for_command():
    """
    Listens for a command from the user via the microphone and returns the transcribed text.
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening...")

        try:
            # Listen for speech, with a timeout to avoid waiting forever
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Recognizing speech...")

            # Recognize speech using the Google Web Speech API
            # This is a good default choice as it's free and generally accurate.
            # It does require an internet connection.
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text

        except sr.WaitTimeoutError:
            print("No speech detected within the timeout period.")
            return None
        except sr.UnknownValueError:
            print("Google Web Speech API could not understand the audio.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Web Speech API; {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during listening: {e}")
            return None

if __name__ == '__main__':
    # This is for testing the module directly
    print("--- Testing listening.py ---")
    print("Say something, and the module will try to recognize it.")

    # Simple loop to test listening
    while True:
        command = listen_for_command()
        if command:
            print(f"Recognized command: '{command}'")
            if "stop listening" in command.lower():
                print("Stopping listening test.")
                break
        else:
            print("Didn't catch that. Please try again.")