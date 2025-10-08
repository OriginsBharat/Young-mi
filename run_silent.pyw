# run_silent.pyw
# This script launches the main application in a detached process
# without a console window, making it suitable for automatic startup.

import subprocess
import os
import sys

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
main_script_path = os.path.join(script_dir, "main.py")

# Use DETACHED_PROCESS to run the script in the background without a console
# This is a Windows-specific creation flag.
DETACHED_PROCESS = 0x00000008

# The command to execute: pythonw.exe is used to ensure no console pops up
# for the main script either.
command = [sys.executable.replace('python.exe', 'pythonw.exe'), main_script_path]

# Launch the main application
subprocess.Popen(command, creationflags=DETACHED_PROCESS, close_fds=True)