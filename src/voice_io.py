# src/voice_io.py

import speech_recognition as sr
from TTS.api import TTS
import torch
import sounddevice as sd
import numpy as np
import os

class VoiceIO:
    # Define constants for audio recording to ensure consistency
    SAMPLE_RATE = 16000  # 16kHz is standard for speech recognition
    CHANNELS = 1
    DTYPE = 'int16'
    SAMPLE_WIDTH = 2     # Corresponds to 'int16' (2 bytes)

    def __init__(self, voice_clone_path=None, device=None):
        self.recognizer = sr.Recognizer()
        # Set a static energy threshold. This may need tuning based on the user's mic.
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = False

        # Determine the best device for TTS (GPU if available)
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"Using device: {self.device} for TTS.")
        try:
            # This will download the XTTS model on the first run, which can take time.
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            self.voice_clone_path = voice_clone_path
            if self.voice_clone_path and not os.path.exists(self.voice_clone_path):
                print(f"[WARNING] Voice clone sample not found at: {self.voice_clone_path}. Using default speaker.")
                self.voice_clone_path = None
        except Exception as e:
            print(f"Error initializing Coqui TTS: {e}\nText-to-speech will be disabled.")
            self.tts = None

    def speak(self, text, language="en"):
        """Converts text to speech using Coqui XTTS and plays it with sounddevice."""
        if not self.tts:
            print(f"TTS Disabled: {text}")
            return

        print(f"Kim Young-mi is speaking: {text}")
        try:
            # XTTS inference.
            # If a voice clone path is provided and exists, use it.
            # Otherwise, fall back to a default built-in speaker.
            speaker_to_use = self.voice_clone_path if self.voice_clone_path else None
            speaker_id_to_use = None if speaker_to_use else "Ana Florence"

            wav = self.tts.tts(
                text=text,
                speaker_wav=speaker_to_use,
                speaker=speaker_id_to_use,
                language=language
            )
            # XTTS model output is at 24000Hz
            sd.play(np.array(wav), samplerate=24000)
            sd.wait()
        except Exception as e:
            print(f"Error during TTS generation or playback: {e}")

    def listen(self, duration=5):
        """
        Records audio from the default microphone for a fixed duration using sounddevice,
        then performs speech recognition. This method bypasses the need for PyAudio.
        """
        print(f"Listening for {duration} seconds... Speak now.")
        try:
            recording = sd.rec(int(duration * self.SAMPLE_RATE), samplerate=self.SAMPLE_RATE, channels=self.CHANNELS, dtype=self.DTYPE)
            sd.wait()  # Wait until recording is finished
        except Exception as e:
            print(f"An error occurred during audio recording: {e}")
            return None

        # Convert the NumPy array from sounddevice into the AudioData object SpeechRecognition expects
        audio_data = sr.AudioData(recording.tobytes(), self.SAMPLE_RATE, self.SAMPLE_WIDTH)

        try:
            print("Recognizing speech...")
            text = self.recognizer.recognize_google(audio_data)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I could not understand what you said.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return None

if __name__ == '__main__':
    # This block is for testing the module directly
    print("Initializing Voice I/O with Coqui XTTS and SoundDevice...")
    # To test cloning, create a 'sample.wav' file in the root directory.
    # A clear, 5-15 second sample of a single speaker works best.
    voice = VoiceIO(voice_clone_path='sample.wav')

    if voice.tts:
        voice.speak("Hello babe. My voice is working now. Say something, I'll listen for 5 seconds.")

        user_input = voice.listen()
        if user_input:
            voice.speak(f"I heard you say: {user_input}. Is that right?")
        else:
            voice.speak("I didn't quite catch that. Could you try again?")
    else:
        print("\nTTS engine failed to initialize. Cannot test speaking.")