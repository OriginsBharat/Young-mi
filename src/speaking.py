import torch
from TTS.api import TTS
import sounddevice as sd
import numpy as np
import os
from dotenv import load_dotenv

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
    """Initializes the Coqui TTS engine."""
    global tts_engine
    if tts_engine is None:
        print("[INFO] Initializing Text-to-Speech engine...")
        try:
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
            tts_engine = TTS(model_name, gpu=(device == "cuda"))
            print("[INFO] TTS engine initialized successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to initialize TTS engine: {e}")

def toggle_team_chat():
    """Toggles the team voice chat feature on and off."""
    global team_chat_enabled
    if not VIRTUAL_AUDIO_DEVICE_ID:
        print("[ERROR] Cannot enable team chat: VIRTUAL_AUDIO_DEVICE_ID is not set.")
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
        print("[ERROR] TTS engine is not initialized. Cannot speak.")
        return

    speaker_wav_path = CUSTOM_SPEAKER_FILE if os.path.exists(CUSTOM_SPEAKER_FILE) else None
    output_device = sd.default.device[1]
    text_to_speak = text

    if team_chat_enabled and not force_default_device:
        print(f"[INFO] Original thought for team chat: '{text}'")
        sanitizer_prompt = (f"Rephrase the following thought into a clear, concise, and impersonal tactical callout "
                            f"suitable for a competitive Valorant team voice chat. Remove all personal pet names, "
                            f"loving language, or emotional content. Just the facts.\n\nThought: '{text}'")

        sanitized_text = thinking.get_ai_response(sanitizer_prompt, [])
        text_to_speak = sanitized_text
        print(f"[INFO] Sanitized callout: '{text_to_speak}'")

        try:
            output_device = int(VIRTUAL_AUDIO_DEVICE_ID)
        except (TypeError, ValueError):
            print(f"[ERROR] Invalid VIRTUAL_AUDIO_DEVICE_ID. Using default device.")

    try:
        print(f"[INFO] Generating speech for: '{text_to_speak}'")
        wav = tts_engine.tts(text=text_to_speak, speaker_wav=speaker_wav_path, language="en", split_sentences=True)
        sd.play(np.array(wav), samplerate=24000, device=output_device)
        sd.wait()

    except Exception as e:
        print(f"[ERROR] An error occurred during text-to-speech generation or playback: {e}")

if __name__ == '__main__':
    print("--- Testing speaking.py (Definitive Version) ---")
    thinking.load_character_sheet()
    initialize_tts()

    if tts_engine:
        original_thought = "Nice one, babe! That makes it a 4v5, huge advantage for us now."
        toggle_team_chat()
        speak(original_thought)
        toggle_team_chat()
    else:
        print("Could not run speaking test because TTS engine failed to initialize.")