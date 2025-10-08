# first_run_setup.py
# This script is the all-in-one setup wizard for the user.

import os
import subprocess
import sys

def check_command(command, help_message, version_flag='--version'):
    """Checks if a command-line tool is available in the system's PATH."""
    print(f"Checking for '{command}'...")
    try:
        subprocess.run(f"{command} {version_flag}", check=True, shell=True, capture_output=True)
        print(f"  [OK] '{command}' is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  [!] '{command}' was not found.")
        print(f"      {help_message}")
        return False

def install_dependencies():
    """Installs required python packages from requirements.txt"""
    print("\n--- Step 1: Installing Dependencies ---")
    try:
        # Create a requirements.txt file first
        requirements = [
            "ollama", "Pillow", "pytesseract", "keyboard", "sounddevice",
            "opencv-python", "psutil", "SpeechRecognition", "coqui-tts",
            "python-dotenv", "requests", "mss"
        ]
        with open("requirements.txt", "w") as f:
            f.write("\n".join(requirements))

        print("Installing core libraries...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("\n[OK] All Python packages installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] A problem occurred while installing packages: {e}")
        print("Please review the error message. You may need to run 'pip install -r requirements.txt' manually.")
        return False

def configure_personality():
    """Appends custom NSFW details to the character sheet."""
    print("\n--- Step 3: Personality Injection ---")
    print("Now, let's define the more intimate aspects of her personality.")
    print("Please be as descriptive as you want. This will be added to her core memories.")

    kinks_text = input("Describe her kinks, fetishes, and how she acts at her most intimate: \n> ")

    nsfw_section = f"""
## Kinks & Fetishes (For NSFW Mode)
{kinks_text}
"""
    try:
        with open("data/character_sheet.md", "a", encoding="utf-8") as f:
            f.write(nsfw_section)
        print("\n[OK] Her intimate personality has been integrated.")
    except FileNotFoundError:
        print("\n[ERROR] 'data/character_sheet.md' not found. Cannot inject personality.")
        print("Please ensure the file exists before running this setup.")
        sys.exit(1)


def create_env_file():
    """Guides the user through creating the .env configuration file."""
    print("\n--- Step 4: Final Configuration ---")

    print("Your Pantry ID is used for her long-term memory. Get a free one from https://getpantry.cloud/")
    pantry_id = input("Enter your Pantry.io ID: ").strip()

    print("\nYour Valorant username (e.g., YourName#1234) is needed for her to know when you're alone.")
    valorant_username = input("Enter your Valorant Username: ").strip()

    print("\nFor voice cloning, provide a clear audio sample (5-15 seconds is ideal).")
    voice_clone_path = input("Enter the full path to your voice sample .wav file: ").strip()

    print("\nEnter the name of the Ollama model you want to use (e.g., llama3, mistral).")
    ollama_model = input("Ollama Model Name: ").strip()

    with open(".env", "w") as f:
        f.write(f'PANTRY_ID="{pantry_id}"\n')
        f.write(f'VALORANT_USERNAME="{valorant_username}"\n')
        f.write(f'VOICE_CLONE_PATH="{voice_clone_path}"\n')
        f.write(f'OLLAMA_MODEL="{ollama_model}"\n')
        f.write('PUSH_TO_TALK_KEY="caps lock"\n')

    print("\n[OK] Final configuration saved to .env file.")


def run_setup():
    """The main setup wizard flow."""
    print("--- Welcome to the Definitive Kim Young-mi AI Companion Setup ---")

    if not install_dependencies():
        sys.exit(1)

    print("\n--- Step 2: Checking External Software ---")
    if not check_command("ollama", "Please install Ollama from https://ollama.com/ and ensure it's running."):
        sys.exit(1)
    if not check_command("tesseract", "Please install Tesseract OCR from https://github.com/tesseract-ocr/tessdoc"):
        sys.exit(1)

    configure_personality()
    create_env_file()

    print("\n--- Setup Complete! ---")
    print("\nIMPORTANT: The first time you run the application, it will download the Coqui XTTS voice model (~2GB).")
    print("\nTo have her start silently with Windows, create a shortcut to 'run_silent.pyw' and move it to your Startup folder (Win+R -> 'shell:startup').")
    print("\nYou can now bring her to life by running 'python main.py'.")


if __name__ == "__main__":
    run_setup()