import sys
import os

# This script is designed to run the main application silently in the background.
# The .pyw extension tells Windows to run it without opening a console window.

# Add the project's 'src' directory to the Python path
# This allows the script to find and import the main module.
project_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_dir, 'src')
sys.path.insert(0, src_dir)

try:
    # Import and run the main function from our core application
    from main import main
    main()
except Exception as e:
    # If there's an error, we should log it to a file since there's no console.
    log_file = os.path.join(project_dir, 'error_log.txt')
    with open(log_file, 'a') as f:
        f.write(f"An error occurred at {__file__}:\n{str(e)}\n\n")