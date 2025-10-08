# first_run_setup.py
# This script is the all-in-one setup wizard for the user.

import os
import subprocess
import sys

def check_command(command, help_message, version_flag='--version'):
    """Checks if a command-line tool is available in the system's PATH."""
    print(f"Checking for '{command}'...")
    try:
        # Use shell=True for Windows compatibility, though it's less secure.
        # Given this is a user-run script, it's an acceptable tradeoff.
        subprocess.run(f"{command} {version_flag}", check=True, shell=True, capture_output=True)
        print(f"  [OK] '{command}' is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  [!] '{command}' was not found.")
        print(f"      {help_message}")
        return False

def install_dependencies():
    """Installs required python packages from requirements.txt"""
    print("\n--- Step 1: Installing Python Packages ---")
    try:
        # First, ensure numpy and torch are installed, as they are often prerequisites
        print("Installing core ML libraries (numpy, torch)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy", "torch"])

        print("\nInstalling remaining application packages...")
        # Use --no-build-isolation to help with complex dependencies
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--no-build-isolation"])

        print("\n[OK] All Python packages installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Failed to install Python packages: {e}")
        print("Please review the error message above. You may need to install a package manually.")
        return False

def create_env_file():
    """Guides the user through creating the .env configuration file."""
    print("\n--- Step 3: Configuring Your Companion ---")

    print("Your Pantry ID is used to give Kim Young-mi a persistent memory.")
    print("You can get a free one from https://getpantry.cloud/")
    pantry_id = input("Enter your Pantry.io ID: ").strip()

    print("\nFor voice cloning, provide a clear audio sample of a single speaker (5-15 seconds is ideal).")
    voice_clone_path = input("Enter the full path to your voice sample .wav file (e.g., C:\\Users\\You\\tashi.wav): ").strip()

    if not os.path.exists(voice_clone_path):
        print("\n[WARNING] The voice file path you provided does not seem to exist.")
        print("The application will use a default voice until you provide a valid path.")
        print("You can fix this by editing the '.env' file later.")

    print("\nEnter the name of the Ollama model you want to use (e.g., llama3, mistral).")
    ollama_model = input("Ollama Model Name: ").strip()

    with open(".env", "w") as f:
        f.write(f'PANTRY_ID="{pantry_id}"\n')
        f.write(f'VOICE_CLONE_PATH="{voice_clone_path}"\n')
        f.write(f'OLLAMA_MODEL="{ollama_model}"\n')
        f.write('PUSH_TO_TALK_KEY="caps lock"\n')

    print("\n[OK] Configuration saved to .env file.")

def run_setup():
    """The main setup wizard flow."""
    print("--- Welcome to the Kim Young-mi AI Companion Setup ---")
    print("This wizard will guide you through installing dependencies and configuring the application.")

    # 1. Install Python dependencies
    if not install_dependencies():
        sys.exit(1)

    # 2. Check for external software
    print("\n--- Step 2: Checking for External Software ---")
    ollama_ok = check_command("ollama", "Please install Ollama from https://ollama.com/ and ensure it's running.")
    tesseract_ok = check_command("tesseract", "Please install Tesseract OCR from https://github.com/tesseract-ocr/tessdoc and add it to your system's PATH.")

    if not (ollama_ok and tesseract_ok):
        print("\nPlease install the required software and run this setup again.")
        sys.exit(1)

    # 3. Configure .env file
    create_env_file()

    # 4. Final instructions
    print("\n--- Setup Complete! ---")
    print("\nIMPORTANT: The first time you run the application, it will download the Coqui XTTS voice model.")
    print("This is a large file (~2GB) and may take some time depending on your internet connection.")
    print("\nYou can now start the application by running 'python main.py'.")
    print("\nTo have Kim Young-mi start silently and automatically with Windows:")
    print("  1. Right-click on the 'run_silent.pyw' file and select 'Create shortcut'.")
    print("  2. Press the Windows Key + R to open the Run dialog.")
    print("  3. Type 'shell:startup' and press Enter. This will open your Startup folder.")
    print("  4. Move the shortcut you created in step 1 into this Startup folder.")
    print("\nEnjoy your time with Kim Young-mi!")


if __name__ == "__main__":
    run_setup()