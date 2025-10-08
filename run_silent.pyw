import sys
import os
import traceback

# This script is designed to run the main application silently in the background.
# The .pyw extension tells Windows to run it without opening a console window.

# Get the absolute path of the directory containing this script.
project_dir = os.path.dirname(os.path.abspath(__file__))

# Add the project's 'src' directory to the Python path.
# This allows the script to find and import the main module.
src_dir = os.path.join(project_dir, 'src')
sys.path.insert(0, src_dir)

# Define a log file path for error handling.
log_file = os.path.join(project_dir, 'error_log.txt')

try:
    # Import and run the main function from our core application.
    from main import main
    main()
except Exception as e:
    # If there's an error during execution, we must log it to a file
    # because there is no console window to display it.
    with open(log_file, 'a') as f:
        f.write(f"--- An error occurred at {__file__} ---\n")
        f.write(traceback.format_exc())
        f.write("\n\n")