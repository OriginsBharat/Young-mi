# src/voice_io.py
# This module handles all audio input and output in a non-blocking way.

import speech_recognition as sr
from TTS.api import TTS
import torch
import sounddevice as sd
import numpy as np
import os
import queue
import threading
import sys
import time

class VoiceIO(threading.Thread):
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'int16'
    SAMPLE_WIDTH = 2

    def __init__(self, voice_clone_path=None, device=None):
        super().__init__()
        self.daemon = True
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = False

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"Using device: {self.device} for TTS.")
        try:
            os.environ["COQUI_TOS_AGREED"] = "1"
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            self.voice_clone_path = voice_clone_path
            if self.voice_clone_path and not os.path.exists(self.voice_clone_path):
                print(f"[WARNING] Voice clone sample not found at: {self.voice_clone_path}. Using default speaker.")
                self.voice_clone_path = None
        except Exception as e:
            print(f"Error initializing Coqui TTS: {e}\nText-to-speech will be disabled.")
            self.tts = None

        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()

    def _audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def run(self):
        """Opens the microphone stream and keeps it running."""
        print("[Audio Stream Thread] Started.")
        try:
            with sd.RawInputStream(samplerate=self.SAMPLE_RATE, blocksize=8000,
                                   dtype=self.DTYPE, channels=self.CHANNELS,
                                   callback=self._audio_callback):
                while not self.stop_event.is_set():
                    time.sleep(0.1)
        except Exception as e:
            print(f"[Audio Stream Thread ERROR] {e}")
        print("[Audio Stream Thread] Stopped.")

    def stop(self):
        """Signals the audio stream to stop."""
        self.stop_event.set()

    def _play_audio(self, wav):
        """Plays audio in a blocking manner. To be run in a separate thread."""
        try:
            sd.play(np.array(wav), samplerate=24000)
            sd.wait()
        except Exception as e:
            print(f"Error during audio playback: {e}")

    def speak(self, text, language="en"):
        """Generates speech and plays it in a non-blocking background thread."""
        if not self.tts:
            print(f"TTS Disabled: {text}")
            return

        print(f"Kim Young-mi is speaking: {text}")
        try:
            speaker_wav = self.voice_clone_path if self.voice_clone_path else None
            speaker = None if speaker_wav else "Ana Florence"
            wav = self.tts.tts(text=text, speaker_wav=speaker_wav, speaker=speaker, language=language)

            # Play the audio in a separate thread so the main loop doesn't block
            playback_thread = threading.Thread(target=self._play_audio, args=(wav,))
            playback_thread.daemon = True
            playback_thread.start()

        except Exception as e:
            print(f"Error during TTS generation: {e}")

    def recognize_audio(self, audio_data):
        """Performs speech recognition on a chunk of audio data."""
        if not audio_data:
            return None

        full_audio = b''.join(audio_data)
        audio_data_obj = sr.AudioData(full_audio, self.SAMPLE_RATE, self.SAMPLE_WIDTH)

        try:
            print("Recognizing speech...")
            text = self.recognizer.recognize_google(audio_data_obj)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I could not understand what you said.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google service; {e}")
            return None