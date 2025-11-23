"""
Runtime hook to set Qt plugin path for PySide6
This ensures qwindows.dll and other Qt plugins are found at runtime
"""
import os
import sys

# In a PyInstaller bundle, sys._MEIPASS contains the path to the bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    # Set Qt plugin path to the PySide6/plugins directory in the bundle
    qt_plugin_path = os.path.join(bundle_dir, 'PySide6', 'plugins')
    if os.path.isdir(qt_plugin_path):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path
    # Also try alternative location
    qt_plugin_path_alt = os.path.join(bundle_dir, 'plugins')
    if os.path.isdir(qt_plugin_path_alt):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path_alt
