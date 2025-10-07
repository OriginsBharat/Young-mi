import sounddevice as sd
import os
from dotenv import set_key, find_dotenv

# This script helps the user configure Voicemeeter for team voice chat.

def select_audio_device():
    """Lists available audio devices and prompts the user to select one."""
    print("\n--- Team Voice Chat Setup ---")
    print("This will help me talk to your teammates when you allow it.")
    print("For this to work, you need a virtual audio mixer installed.")
    print("The recommended free option is Voicemeeter: https://vb-audio.com/Voicemeeter/")
    print("\nPlease install the standard 'Voicemeeter' version and restart your computer before continuing.")

    input("\nPress Enter when you have installed Voicemeeter and are ready to proceed...")

    try:
        devices = sd.query_devices()
        output_devices = [dev for dev in devices if dev['max_output_channels'] > 0]
    except Exception as e:
        print(f"\n[ERROR] Could not list audio devices: {e}")
        return None

    print("\n--- Available Audio Output Devices ---")
    for dev in output_devices:
        print(f"  ID: {dev['index']}, Name: {dev['name']}")

    print("----------------------------------------")
    print("Please look for 'Voicemeeter Input' or a similarly named device in the list.")

    while True:
        try:
            device_id_str = input("Enter the ID number of the 'Voicemeeter Input' device: ").strip()
            device_id = int(device_id_str)
            chosen_device = next((dev for dev in output_devices if dev['index'] == device_id), None)

            if chosen_device:
                print(f"\nGreat! You have selected: {chosen_device['name']}")
                return str(device_id)
            else:
                print("Invalid ID. Please choose a valid ID from the list above.")
        except ValueError:
            print("Invalid input. Please enter a numeric ID.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

def save_device_to_env(device_id):
    """Saves the selected device ID to the .env file."""
    try:
        env_path = find_dotenv()
        if not env_path:
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            print("Note: .env file not found. I will create one for you.")
            open(env_path, 'a').close()

        set_key(env_path, "VIRTUAL_AUDIO_DEVICE_ID", device_id)
        print(f"[SUCCESS] Saved VIRTUAL_AUDIO_DEVICE_ID={device_id} to your .env file.")
        return True
    except Exception as e:
        print(f"[ERROR] Could not save to .env file: {e}")
        return False

if __name__ == "__main__":
    device = select_audio_device()
    if device:
        if save_device_to_env(device):
            print("\nSetup complete! I now know how to talk to your team.")

    input("\nPress Enter to exit.")