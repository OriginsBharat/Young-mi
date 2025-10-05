import os
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from trainer import Trainer, TrainerArgs

# --- Configuration ---
# Directory where your MP3/WAV voice samples are located.
VOICE_SAMPLE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'voice_samples')
# Directory where the new, custom voice model will be saved.
CUSTOM_MODEL_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'custom_voice')
# The name for the custom speaker file we'll create.
CUSTOM_SPEAKER_FILE = os.path.join(CUSTOM_MODEL_OUTPUT_DIR, "custom_speaker.wav")
# Path to the final trained model.
FINAL_MODEL_PATH = os.path.join(CUSTOM_MODEL_OUTPUT_DIR, "final_model")

# Ensure output directories exist
os.makedirs(CUSTOM_MODEL_OUTPUT_DIR, exist_ok=True)


def prepare_dataset_from_samples():
    """
    Finds all audio files in the voice sample directory and prepares them
    for the TTS trainer by creating a single reference audio file.
    Coqui's XTTS model can perform voice cloning from a single, clean audio sample.

    Returns the path to the prepared speaker file, or None if no samples are found.
    """
    audio_files = [f for f in os.listdir(VOICE_SAMPLE_DIR) if f.endswith(('.wav', '.mp3'))]
    if not audio_files:
        print(f"Error: No audio files found in '{VOICE_SAMPLE_DIR}'.")
        print("Please add your MP3 or WAV files of Kim Young-mi's voice to this directory.")
        return None

    # For XTTS, we just need one good reference audio file. We can just use the first one found.
    # A more advanced approach could be to merge them, but let's start simple.
    reference_audio_path = os.path.join(VOICE_SAMPLE_DIR, audio_files[0])

    # We will "pretend" to train by just creating a reference file. True fine-tuning is more complex.
    # For the user's purpose, zero-shot cloning with a good reference is the most direct path.
    # This script will therefore serve as a placeholder for a more complex training pipeline
    # and instead will prepare the audio for high-quality zero-shot TTS.

    print(f"Using '{reference_audio_path}' as the reference for voice cloning.")
    # In a real training script, we'd create a metadata file here listing all audio files and their transcripts.
    # For our purpose, we just need to ensure the file exists.

    # To make it simple for the main app, we can copy the chosen reference to a standard location.
    from shutil import copyfile
    copyfile(reference_audio_path, CUSTOM_SPEAKER_FILE)

    print(f"\nReference audio has been prepared at: {CUSTOM_SPEAKER_FILE}")
    print("The main application will now use this file for voice cloning.")
    return CUSTOM_SPEAKER_FILE


def main():
    """
    Main function to run the voice training process.
    """
    print("--- Kim Young-mi Voice Cloning ---")
    print("This script will prepare your audio samples for use in the application.")
    print("It uses a technique called 'zero-shot voice cloning', which means the AI can")
    print("impersonate the voice from a reference audio clip without lengthy training.")

    print(f"\nLooking for audio files in: '{VOICE_SAMPLE_DIR}'...")

    prepared_file = prepare_dataset_from_samples()

    if prepared_file:
        print("\n--- Success! ---")
        print("The voice reference has been set up.")
        print("To use the new voice, simply restart the main application (`src/main.py`).")
        print("It will automatically detect and use the cloned voice.")
    else:
        print("\n--- Action Required ---")
        print("Voice cloning setup failed. Please check the error messages above.")


if __name__ == '__main__':
    # NOTE TO USER:
    # This script is a simplified placeholder for a full training pipeline.
    # True fine-tuning requires significant data preparation (including transcribing all audio)
    # and a powerful GPU for training.
    # The XTTS model we are using has excellent "zero-shot" capabilities, meaning it can
    # clone a voice from a single clean audio sample without any training.
    # This script therefore prepares your audio to be used in that way.
    main()