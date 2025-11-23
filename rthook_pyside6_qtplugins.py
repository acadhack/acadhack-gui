import os
import sys

def _setup_qt_directories():
    """
    Configure Qt environment variables for frozen applications.
    Ensures PySide6 plugins are found by the Qt backend.
    """
    # Only run in frozen mode
    if not getattr(sys, 'frozen', False):
        return

    # Get the base directory of the application
    # In a frozen app, sys.executable is the exe path.
    base_dir = os.path.dirname(sys.executable)
    
    # Check if PyInstaller v6+ '_internal' structure is used
    internal_dir = os.path.join(base_dir, '_internal')
    if os.path.exists(internal_dir):
        base_dir = internal_dir

    # Locate the PySide6 plugins directory within the bundle
    # Because we used collect_all, the structure is preserved as PySide6/plugins
    # We check multiple common locations just to be safe
    candidates = [
        os.path.join(base_dir, 'PySide6', 'plugins'),
        os.path.join(base_dir, 'PySide6', 'Qt', 'plugins'),
        os.path.join(base_dir, 'plugins'),
    ]
    
    plugins_dir = None
    for candidate in candidates:
        if os.path.exists(candidate):
            plugins_dir = candidate
            break
    
    # If the plugins directory exists, set the environment variables
    if plugins_dir:
        # Tell Qt where to look for all plugins
        os.environ['QT_PLUGIN_PATH'] = plugins_dir
        # print(f"Set QT_PLUGIN_PATH to: {plugins_dir}")
        
        # Explicitly tell Qt where the platform plugin (qwindows.dll) is
        platforms_dir = os.path.join(plugins_dir, 'platforms')
        if os.path.exists(platforms_dir):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = platforms_dir
            # print(f"Set QT_QPA_PLATFORM_PLUGIN_PATH to: {platforms_dir}")
            
        # Optional: Force the platform to 'windows' if auto-detection fails
        # os.environ['QT_QPA_PLATFORM'] = 'windows'
    else:
        # For debugging: if this prints, collect_all didn't work as expected
        sys.stderr.write(f"WARNING: Could not find Qt plugins in {base_dir}\n")

# Run the setup immediately
_setup_qt_directories()
