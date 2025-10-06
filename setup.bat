@echo off
REM This batch script sets up the Kim Young-mi AI to run silently on Windows startup.

echo --- Kim Young-mi: Invisible Setup for Windows ---
echo This will configure the AI to run silently in the background when you log in.
echo.

REM Get the directory where this script is located.
SET "SCRIPT_DIR=%~dp0"

REM Define the full path to the silent runner script.
SET "TARGET_PATH=%SCRIPT_DIR%run_silent.pyw"

REM Define the name and location for the shortcut in the Startup folder.
SET "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
SET "SHORTCUT_NAME=Kim Young-mi AI.lnk"
SET "SHORTCUT_PATH=%STARTUP_FOLDER%\%SHORTCUT_NAME%"

echo Creating shortcut in your Startup folder...
echo Target: %TARGET_PATH%
echo Shortcut: %SHORTCUT_PATH%
echo.

REM --- Create the Shortcut using a temporary VBScript ---
REM This is a standard method to create shortcuts from a batch file.
SET "VBS_SCRIPT=%TEMP%\create_shortcut.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo sLinkFile = "%SHORTCUT_PATH%" >> "%VBS_SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_SCRIPT%"
echo oLink.TargetPath = "%TARGET_PATH%" >> "%VBS_SCRIPT%"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%VBS_SCRIPT%"
echo oLink.Save >> "%VBS_SCRIPT%"

REM Execute the VBScript
cscript //nologo "%VBS_SCRIPT%"

REM Clean up the temporary VBScript
del "%VBS_SCRIPT%"

echo.
echo --- SETUP COMPLETE ---
echo Kim Young-mi is now set up to start automatically and silently when you log in.
echo To remove her from startup, simply delete the shortcut from this folder:
echo %STARTUP_FOLDER%
echo.
pause