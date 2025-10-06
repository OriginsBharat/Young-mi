import sounddevice as sd
import os
from dotenv import set_key, find_dotenv

# This script helps the user configure the virtual audio cable for team voice chat.

def select_audio_device():
    """Lists available audio devices and prompts the user to select one."""
    print("--- Virtual Audio Setup for Team Chat ---")
    print("\nTo use team voice chat, you need a 'virtual audio cable' installed.")
    print("A popular free option is VB-CABLE: https://vb-audio.com/Cable/")
    print("\nAfter installing it, please run this script again.")

    try:
        devices = sd.query_devices()
        output_devices = [dev for dev in devices if dev['max_output_channels'] > 0]
    except Exception as e:
        print(f"\nCould not list audio devices: {e}")
        print("Please ensure your audio drivers are working correctly.")
        return None

    print("\n--- Available Audio Output Devices ---")
    for i, dev in enumerate(output_devices):
        print(f"ID: {dev['index']}, Name: {dev['name']}")

    print("\n----------------------------------------")
    print("Please look for the 'CABLE Input' or a similarly named virtual device.")

    while True:
        try:
            device_id = input("Enter the ID of the virtual audio device you want to use: ").strip()
            # Find the chosen device to validate it
            chosen_device = next((dev for dev in output_devices if str(dev['index']) == device_id), None)

            if chosen_device:
                print(f"You have selected: {chosen_device['name']}")
                return str(chosen_device['index'])
            else:
                print("Invalid ID. Please choose from the list above.")
        except ValueError:
            print("Invalid input. Please enter a numeric ID.")
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

def save_device_to_env(device_id):
    """Saves the selected device ID to the .env file."""
    try:
        env_path = find_dotenv()
        if not env_path:
            # If .env doesn't exist, create it.
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            open(env_path, 'a').close()
            print("Created a new .env file.")

        set_key(env_path, "VIRTUAL_AUDIO_DEVICE_ID", device_id)
        print(f"Successfully saved VIRTUAL_AUDIO_DEVICE_ID={device_id} to your .env file.")
        return True
    except Exception as e:
        print(f"Error saving to .env file: {e}")
        return False

if __name__ == "__main__":
    device = select_audio_device()
    if device:
        if save_device_to_env(device):
            print("\n--- Setup Complete ---")
            print("I now know which device to use for team chat.")
            print("The final step is to add a hotkey to the main application to toggle this feature.")

    input("\nPress Enter to exit.")