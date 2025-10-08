# run_silent.pyw
# This script launches the main application in a detached process
# without a console window, making it suitable for automatic startup.

import subprocess
import os
import sys

try:
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script_path = os.path.join(script_dir, "main.py")

    # Use DETACHED_PROCESS to run the script in the background without a console
    # This is a Windows-specific creation flag.
    DETACHED_PROCESS = 0x00000008

    # The command to execute: pythonw.exe is used to ensure no console pops up
    # for the main script either.
    pythonw_executable = sys.executable.replace('python.exe', 'pythonw.exe')

    # In some environments, pythonw.exe might not be in the same directory.
    # If it doesn't exist, fall back to the regular python.exe.
    if not os.path.exists(pythonw_executable):
        pythonw_executable = sys.executable

    command = [pythonw_executable, main_script_path]

    # Launch the main application
    subprocess.Popen(command, creationflags=DETACHED_PROCESS, close_fds=True)

except Exception as e:
    # If anything goes wrong, log it to a file in the same directory
    # so the user has some way of debugging startup issues.
    with open(os.path.join(script_dir, "silent_startup_error.log"), "w") as f:
        f.write(f"An error occurred during silent startup:\n")
        f.write(str(e))