import os
import sys

def _setup_qt_directories():
    """
    Configure Qt environment variables for frozen applications.
    Ensures PySide6 plugins are found by the Qt backend.
    """
    # Setup logging
    log_file = "hook_debug.txt"
    if getattr(sys, 'frozen', False):
        log_file = os.path.join(os.path.dirname(sys.executable), "hook_debug.txt")
        
    def log(msg):
        try:
            with open(log_file, "a") as f:
                f.write(f"[HOOK] {msg}\n")
        except: pass

    log("Runtime hook started")

    # Only run in frozen mode
    if not getattr(sys, 'frozen', False):
        log("Not frozen, skipping")
        return

    # Get the base directory of the application
    # In a frozen app, sys.executable is the exe path.
    base_dir = os.path.dirname(sys.executable)
    log(f"Base dir: {base_dir}")
    
    # Check if PyInstaller v6+ '_internal' structure is used
    internal_dir = os.path.join(base_dir, '_internal')
    if os.path.exists(internal_dir):
        base_dir = internal_dir
        log(f"Found _internal dir: {base_dir}")

    # Locate the PySide6 plugins directory within the bundle
    # Because we used collect_all, the structure is preserved as PySide6/plugins
    # We check multiple common locations just to be safe
    candidates = [
        os.path.join(base_dir, 'PySide6', 'plugins'),
        os.path.join(base_dir, 'PySide6', 'Qt', 'plugins'),
        os.path.join(base_dir, 'plugins'),
        os.path.join(base_dir, 'PySide6', 'Qt', 'plugins'), # Duplicate but harmless
    ]
    
    plugins_dir = None
    for candidate in candidates:
        log(f"Checking candidate: {candidate}")
        if os.path.exists(candidate):
            plugins_dir = candidate
            log(f"Found plugins at: {plugins_dir}")
            break
    
    # If the plugins directory exists, set the environment variables
    if plugins_dir:
        # Tell Qt where to look for all plugins
        os.environ['QT_PLUGIN_PATH'] = plugins_dir
        log(f"Set QT_PLUGIN_PATH")
        
        # Explicitly tell Qt where the platform plugin (qwindows.dll) is
        platforms_dir = os.path.join(plugins_dir, 'platforms')
        if os.path.exists(platforms_dir):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = platforms_dir
            log(f"Set QT_QPA_PLATFORM_PLUGIN_PATH to {platforms_dir}")
        else:
            log(f"WARNING: platforms dir not found at {platforms_dir}")
            
        # Optional: Force the platform to 'windows' if auto-detection fails
        # os.environ['QT_QPA_PLATFORM'] = 'windows'
    else:
        # For debugging: if this prints, collect_all didn't work as expected
        log(f"WARNING: Could not find Qt plugins in {base_dir}")
        sys.stderr.write(f"WARNING: Could not find Qt plugins in {base_dir}\n")

# Run the setup immediately
_setup_qt_directories()
