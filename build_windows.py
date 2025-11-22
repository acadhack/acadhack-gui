import os
import subprocess
import sys
import shutil

def build():
    """
    Builds the standalone executable for Windows using PyInstaller.
    """
    # Ensure we are in the script's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Define build arguments
    app_name = "AcadHack"
    main_script = "app_webview.py"
    
    # Icon path (if you have one, otherwise remove this line or ensure the file exists)
    # icon_path = "assets/icon.ico" 
    
    # PyInstaller command arguments
    args = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--windowed",  # Hide console window
        f"--name={app_name}",
        
        # Include the 'web' directory
        "--add-data=web;web",
        
        # Include 'assets' directory if it exists
        "--add-data=assets;assets",
        
        # Hidden imports that might be missed
        "--hidden-import=webview",
        "--hidden-import=clr", # For pythonnet if used by pywebview on Windows
        
        main_script
    ]

    # Add icon if it exists
    if os.path.exists(os.path.join(base_dir, "assets", "icon.ico")):
         args.insert(5, f"--icon=assets/icon.ico")

    print(f"Running: {' '.join(args)}")
    subprocess.check_call(args)

    print("\nBuild complete!")
    print(f"Executable is located in: {os.path.join(base_dir, 'dist', app_name)}")

if __name__ == "__main__":
    build()
