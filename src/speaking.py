import torch
from TTS.api import TTS
import sounddevice as sd
import numpy as np
import os
from dotenv import load_dotenv

# V9: Import the thinking module to sanitize team chat messages
import src.thinking as thinking

# Load environment variables
load_dotenv()

# --- Configuration ---
device = "cuda" if torch.cuda.is_available() else "cpu"
CUSTOM_VOICE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'custom_voice')
CUSTOM_SPEAKER_FILE = os.path.join(CUSTOM_VOICE_DIR, "custom_speaker.wav")
VIRTUAL_AUDIO_DEVICE_ID = os.getenv("VIRTUAL_AUDIO_DEVICE_ID")

# --- Global State ---
tts_engine = None
team_chat_enabled = False

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
        speak("I can't talk to the team, babe. The virtual audio device isn't set up.", force_default_device=True)
        return

    team_chat_enabled = not team_chat_enabled
    status = "on" if team_chat_enabled else "off"
    print(f"--- Team Voice Chat is now {status.upper()} ---")
    speak(f"Okay, team chat is {status}.", force_default_device=True)

def speak(text, force_default_device=False):
    """
    Converts text to speech and plays it on the appropriate device.
    If team chat is on, it will sanitize the message first.
    """
    if tts_engine is None:
        print("TTS engine is not initialized. Cannot speak.")
        return

    speaker_wav_path = CUSTOM_SPEAKER_FILE if os.path.exists(CUSTOM_SPEAKER_FILE) else None
    output_device = sd.default.device
    text_to_speak = text

    if team_chat_enabled and not force_default_device:
        print(f"Original thought for team chat: '{text}'")
        # V9: Sanitize the message for team chat
        sanitizer_prompt = (f"Rephrase the following thought into a clear, concise, and impersonal tactical callout "
                            f"suitable for a competitive Valorant team voice chat. Remove all personal pet names, "
                            f"loving language, or emotional content. Just the facts.\n\nThought: '{text}'")

        # Use a minimal history for this call to keep it fast and focused
        sanitized_text = thinking.get_ai_response(sanitizer_prompt, [])
        text_to_speak = sanitized_text
        print(f"Sanitized callout: '{text_to_speak}'")

        try:
            output_device = int(VIRTUAL_AUDIO_DEVICE_ID)
        except (TypeError, ValueError):
            print(f"Invalid VIRTUAL_AUDIO_DEVICE_ID. Using default device.")
            output_device = sd.default.device

    try:
        print(f"Generating speech for: '{text_to_speak}'")
        wav = tts_engine.tts(text=text_to_speak, speaker_wav=speaker_wav_path, language="en", split_sentences=True)
        sd.play(np.array(wav), samplerate=24000, device=output_device)
        sd.wait()

    except Exception as e:
        print(f"An error occurred during text-to-speech generation or playback: {e}")

if __name__ == '__main__':
    print("--- Testing speaking.py (V9 Team Chat Sanitization) ---")
    thinking.load_character_sheet() # Need to load this for the sanitizer to work
    initialize_tts()

    if tts_engine:
        # Test sanitization
        original_thought = "Nice one, babe! That makes it a 4v5, huge advantage for us now."
        toggle_team_chat()
        speak(original_thought)
        toggle_team_chat()
    else:
        print("Could not run speaking test because TTS engine failed to initialize.")