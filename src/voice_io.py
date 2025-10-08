# src/voice_io.py

import speech_recognition as sr
from TTS.api import TTS
import torch
import sounddevice as sd
import numpy as np
import os

class VoiceIO:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'int16'
    SAMPLE_WIDTH = 2

    def __init__(self, voice_clone_path=None, device=None):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = False

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"Using device: {self.device} for TTS.")
        try:
            # Set the environment variable to auto-agree to the license
            os.environ["COQUI_TOS_AGREED"] = "1"
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            self.voice_clone_path = voice_clone_path
            if self.voice_clone_path and not os.path.exists(self.voice_clone_path):
                print(f"[WARNING] Voice clone sample not found at: {self.voice_clone_path}. Using default speaker.")
                self.voice_clone_path = None
        except Exception as e:
            print(f"Error initializing Coqui TTS: {e}\nText-to-speech will be disabled.")
            self.tts = None

    def speak(self, text, language="en"):
        if not self.tts:
            print(f"TTS Disabled: {text}")
            return

        print(f"Kim Young-mi is speaking: {text}")
        try:
            # If a voice clone path is provided and exists, use it. Otherwise, use a default speaker.
            speaker_wav = self.voice_clone_path if self.voice_clone_path else None
            speaker = None if speaker_wav else "Ana Florence"

            wav = self.tts.tts(
                text=text,
                speaker_wav=speaker_wav,
                speaker=speaker,
                language=language
            )
            sd.play(np.array(wav), samplerate=24000)
            sd.wait()
        except Exception as e:
            print(f"Error during TTS generation or playback: {e}")

    def listen(self, duration=5):
        print(f"Listening for {duration} seconds... Speak now.")
        try:
            recording = sd.rec(int(duration * self.SAMPLE_RATE), samplerate=self.SAMPLE_RATE, channels=self.CHANNELS, dtype=self.DTYPE)
            sd.wait()
        except Exception as e:
            print(f"An error occurred during audio recording: {e}")
            return None

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