import os
from shutil import copyfile

# This script prepares the user's audio samples for voice cloning.

# --- Configuration ---
VOICE_SAMPLE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'voice_samples')
CUSTOM_MODEL_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'custom_voice')
CUSTOM_SPEAKER_FILE = os.path.join(CUSTOM_MODEL_OUTPUT_DIR, "custom_speaker.wav")

def prepare_dataset_from_samples():
    """
    Finds the first audio file in the voice sample directory and copies it
    to a standard location to be used as a reference for voice cloning.
    Coqui's XTTS model can perform high-quality zero-shot cloning from a single sample.
    """
    os.makedirs(CUSTOM_MODEL_OUTPUT_DIR, exist_ok=True)

    try:
        audio_files = [f for f in os.listdir(VOICE_SAMPLE_DIR) if f.endswith(('.wav', '.mp3'))]
        if not audio_files:
            print(f"[ERROR] No audio files found in '{VOICE_SAMPLE_DIR}'.")
            return False

        reference_audio_path = os.path.join(VOICE_SAMPLE_DIR, audio_files[0])
        print(f"[INFO] Using '{reference_audio_path}' as the reference for voice cloning.")

        # Copy the chosen reference to a standard location for the main app to find.
        copyfile(reference_audio_path, CUSTOM_SPEAKER_FILE)

        print(f"[SUCCESS] Reference audio has been prepared at: {CUSTOM_SPEAKER_FILE}")
        return True
    except Exception as e:
        print(f"[ERROR] An error occurred during voice sample preparation: {e}")
        return False

if __name__ == "__main__":
    print("--- Kim Young-mi: Voice Cloning Setup ---")

    if prepare_dataset_from_samples():
        print("\nVoice cloning reference has been set up successfully.")
    else:
        print("\nVoice cloning setup failed. Please check the error messages above.")

    input("\nPress Enter to exit.")