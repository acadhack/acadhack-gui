"""
Runtime hook to set Qt plugin path for PySide6
This ensures qwindows.dll and other Qt plugins are found at runtime
"""
import os
import sys

        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path
    # Also try alternative location
    qt_plugin_path_alt = os.path.join(bundle_dir, 'plugins')
    if os.path.isdir(qt_plugin_path_alt):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path_alt
