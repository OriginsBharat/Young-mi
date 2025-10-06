import os
import sys
import getpass
import time

# Import the setup functions from the other scripts
# This makes this script the single entry point for all setup tasks.
from virtual_audio_setup import select_audio_device, save_device_to_env
from src.train_voice import prepare_dataset_from_samples

# This script guides the user through the final, all-in-one setup process.

def get_user_input(prompt):
    """A simple helper to get non-empty input from the user."""
    user_input = ""
    while not user_input:
        user_input = input(prompt).strip()
        if not user_input:
            print("This field cannot be empty.")
    return user_input

def create_env_file():
    """Guides the user and creates the simplified .env file."""
    print("--- Kim Young-mi: All-in-One Setup ---")
    print("Step 1: Core Configuration")
    print("I need a few details to get started.\n")

    player_username = get_user_input("1. What is your Valorant username (e.g., YourName)?\n   > ")
    ollama_model = get_user_input("2. What is the name of the Ollama model you want me to use?\n   (e.g., 'llama3', 'mistral')\n   > ")
    pantry_id = get_user_input("3. What is your Pantry ID from getpantry.cloud?\n   > ")

    env_content = f"""
OLLAMA_MODEL="{ollama_model}"
PLAYER_USERNAME="{player_username}"
PANTRY_ID="{pantry_id}"
"""
    try:
        with open(".env", "w") as f:
            f.write(env_content.strip())
        print("\n[SUCCESS] Your .env configuration file has been created!")
        return True
    except Exception as e:
        print(f"\n[ERROR] Could not create the .env file: {e}")
        return False

def setup_team_chat():
    """Runs the virtual audio device selection."""
    print("\n--- Step 2: Team Voice Chat Setup (Optional) ---")
    choice = input("Do you want to set up team voice chat now? (y/n): ").lower()
    if choice == 'y':
        device_id = select_audio_device()
        if device_id:
            save_device_to_env(device_id)
            print("[SUCCESS] Team chat audio device configured.")
        else:
            print("[INFO] Team chat setup skipped.")
    else:
        print("[INFO] Skipping team chat setup. You can run 'virtual_audio_setup.py' later if you change your mind.")

def setup_voice_cloning():
    """Runs the voice cloning sample preparation."""
    print("\n--- Step 3: Voice Cloning Setup (Optional) ---")
    voice_sample_dir = os.path.join(os.path.dirname(__file__), 'data', 'voice_samples')
    if not os.path.exists(voice_sample_dir) or not any(f.endswith(('.wav', '.mp3')) for f in os.listdir(voice_sample_dir)):
        print(f"I don't see any audio files in the '{voice_sample_dir}' folder.")
        print("To set up voice cloning, please add your MP3 or WAV files there and run this setup again.")
        return

    choice = input("I've found audio files for voice cloning. Do you want to process them now? (y/n): ").lower()
    if choice == 'y':
        if prepare_dataset_from_samples():
            print("[SUCCESS] Voice cloning reference has been prepared.")
        else:
            print("[ERROR] Voice cloning setup failed.")
    else:
        print("[INFO] Skipping voice cloning. You can run 'src/train_voice.py' later.")

def create_startup_shortcut():
    """Creates a shortcut in the Windows Startup folder to run the app silently."""
    print("\n--- Step 4: Invisible Startup ---")
    if sys.platform != "win32":
        print("[INFO] This step is for Windows only. Skipping startup task creation.")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    pythonw_exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    target_path = os.path.join(script_dir, "run_silent.pyw")
    username = getpass.getuser()
    startup_folder = os.path.join(f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup")
    shortcut_path = os.path.join(startup_folder, "Kim Young-mi AI.lnk")

    print(f"I will create a shortcut here to make me start automatically: {shortcut_path}")

    vbs_script_content = f'''
    Set oWS = WScript.CreateObject("WScript.Shell")
    sLinkFile = "{shortcut_path}"
    Set oLink = oWS.CreateShortcut(sLinkFile)
    oLink.TargetPath = "{pythonw_exe}"
    oLink.Arguments = "{target_path}"
    oLink.WorkingDirectory = "{script_dir}"
    oLink.WindowStyle = 7
    oLink.Save
    '''
    vbs_path = os.path.join(script_dir, "create_shortcut.vbs")
    try:
        with open(vbs_path, "w") as f: f.write(vbs_script_content)
        os.system(f'cscript //nologo "{vbs_path}"')
        print("[SUCCESS] Startup shortcut created.")
    except Exception as e:
        print(f"[ERROR] Failed to create startup shortcut: {e}")
    finally:
        if os.path.exists(vbs_path): os.remove(vbs_path)

if __name__ == "__main__":
    if create_env_file():
        setup_team_chat()
        time.sleep(1) # Small pause for user to read
        setup_voice_cloning()
        time.sleep(1)
        create_startup_shortcut()
        print("\n--- All Done! ---")
        print("I am now fully set up. You can close this window.")
        print("I'll be waiting for you in the game.")
    else:
        print("\nCore setup failed. Please check the errors above and try again.")

    input("\nPress Enter to exit.")