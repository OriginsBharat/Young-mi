import torch
from TTS.api import TTS
import sounddevice as sd
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
device = "cuda" if torch.cuda.is_available() else "cpu"
CUSTOM_VOICE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'custom_voice')
CUSTOM_SPEAKER_FILE = os.path.join(CUSTOM_VOICE_DIR, "custom_speaker.wav")
VIRTUAL_AUDIO_DEVICE_ID = os.getenv("VIRTUAL_AUDIO_DEVICE_ID")

# --- Global State ---
tts_engine = None
team_chat_enabled = False # V6: State for team chat

def initialize_tts():
    """Initializes the TTS engine."""
    global tts_engine
    if tts_engine is None:
        print("Initializing Text-to-Speech engine...")
        try:
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
            tts_engine = TTS(model_name, gpu=(device == "cuda"))
            print("TTS engine initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize TTS engine: {e}")

def toggle_team_chat():
    """Toggles the team voice chat feature on and off."""
    global team_chat_enabled
    if not VIRTUAL_AUDIO_DEVICE_ID:
        print("Cannot enable team chat: VIRTUAL_AUDIO_DEVICE_ID is not set.")
        print("Please run `virtual_audio_setup.py` first.")
        return

    team_chat_enabled = not team_chat_enabled
    status = "ENABLED" if team_chat_enabled else "DISABLED"
    print(f"--- Team Voice Chat is now {status} ---")
    # Provide feedback through the normal speakers
    speak(f"Team chat {status.lower()}.", force_default_device=True)

def speak(text, force_default_device=False):
    """
    Converts text to speech and plays it on the appropriate device.
    - text: The text to be spoken.
    - force_default_device: If True, always play on the default speakers, ignoring the team chat setting.
    """
    if tts_engine is None:
        print("TTS engine is not initialized. Cannot speak.")
        return

    speaker_wav_path = CUSTOM_SPEAKER_FILE if os.path.exists(CUSTOM_SPEAKER_FILE) else None

    # V6: Determine the output device
    output_device = sd.default.device
    if team_chat_enabled and not force_default_device:
        try:
            output_device = int(VIRTUAL_AUDIO_DEVICE_ID)
            print(f"Redirecting audio to virtual device: {output_device}")
        except (TypeError, ValueError):
            print(f"Invalid VIRTUAL_AUDIO_DEVICE_ID: '{VIRTUAL_AUDIO_DEVICE_ID}'. Using default device.")
            output_device = sd.default.device

    try:
        print(f"Generating speech for: '{text}'")
        wav = tts_engine.tts(text=text, speaker_wav=speaker_wav_path, language="en", split_sentences=True)

        # Play the audio on the selected device
        sd.play(np.array(wav), samplerate=24000, device=output_device)
        sd.wait()

    except Exception as e:
        print(f"An error occurred during text-to-speech generation or playback: {e}")

if __name__ == '__main__':
    print("--- Testing speaking.py (with Team Chat) ---")
    initialize_tts()

    if tts_engine:
        speak("Testing default audio output.", force_default_device=True)

        print("\n--- Testing Team Chat Toggle ---")
        toggle_team_chat() # Try to enable
        if team_chat_enabled:
            speak("This message should be on the virtual audio cable.")
            toggle_team_chat() # Disable again
            speak("And this should be back on the default speakers.")
    else:
        print("Could not run speaking test because TTS engine failed to initialize.")