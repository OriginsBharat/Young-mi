import torch
from TTS.api import TTS
import sounddevice as sd
import numpy as np
import os

# --- Configuration ---
# Determine the appropriate device (use CUDA if available, otherwise CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"

# Path to the directory where the custom voice model is stored
CUSTOM_VOICE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'custom_voice')
# Path to the reference audio file for the custom voice
CUSTOM_SPEAKER_FILE = os.path.join(CUSTOM_VOICE_DIR, "custom_speaker.wav")

# Global variable to hold the TTS object
tts_engine = None

def initialize_tts():
    """
    Initializes the TTS engine. This can take a moment as it downloads the model.
    """
    global tts_engine
    if tts_engine is None:
        print("Initializing Text-to-Speech engine...")
        try:
            # Using a high-quality, multi-lingual model that is excellent for voice cloning
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
            tts_engine = TTS(model_name, gpu=(device == "cuda"))
            print("TTS engine initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize TTS engine: {e}")

def speak(text):
    """
    Converts text to speech and plays it.
    It will automatically use the custom cloned voice if it exists.
    - text: The text to be spoken.
    """
    if tts_engine is None:
        print("TTS engine is not initialized. Cannot speak.")
        return

    # Check if the custom voice file exists
    speaker_wav_path = None
    if os.path.exists(CUSTOM_SPEAKER_FILE):
        speaker_wav_path = CUSTOM_SPEAKER_FILE
        # print(f"Custom voice found. Using '{CUSTOM_SPEAKER_FILE}' for cloning.")
    else:
        # print("No custom voice found. Using default voice.")
        pass

    try:
        print(f"Generating speech for: '{text}'")
        # Generate the waveform, providing the speaker_wav for voice cloning if it exists
        wav = tts_engine.tts(text=text, speaker_wav=speaker_wav_path, language="en", split_sentences=True)

        # Play the audio
        sample_rate = 24000  # XTTS models typically output at 24kHz
        sd.play(np.array(wav), samplerate=sample_rate)
        sd.wait() # Wait until the audio has finished playing
        # print("Finished speaking.")

    except Exception as e:
        print(f"An error occurred during text-to-speech generation or playback: {e}")

if __name__ == '__main__':
    print("--- Testing speaking.py (with Voice Cloning) ---")
    initialize_tts()

    if tts_engine:
        # Test with default voice
        print("\nSpeaking with the default voice...")
        speak("Hello, this is the standard voice.")

        # Check for custom voice and test it
        if os.path.exists(CUSTOM_SPEAKER_FILE):
            print("\nNow speaking with the custom cloned voice...")
            speak("Hello, this should sound like Kim Young-mi. I hope it sounds right to you.")
        else:
            print("\n--- Action Required ---")
            print(f"Custom speaker file not found at '{CUSTOM_SPEAKER_FILE}'.")
            print("To test voice cloning, run the 'src/train_voice.py' script first.")
            print("Make sure you have placed your MP3/WAV files in 'data/voice_samples'.")
    else:
        print("Could not run speaking test because TTS engine failed to initialize.")