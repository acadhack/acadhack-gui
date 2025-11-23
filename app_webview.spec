# -*- mode: python ; coding: utf-8 -*-
"""
Robust PyInstaller spec file for AcadHack GUI application.
Targets: Windows with PySide6, pywebview, and selenium.

Key improvements:
1. Automatic PySide6 plugin discovery (no manual path hacking)
2. Proper runtime hook for QT_PLUGIN_PATH
3. Minimal hidden imports (lets PyInstaller resolve dependencies)
4. Proper exclusions to prevent bloat
5. OneDir mode for easier debugging (PySide6 plugins must be external)
6. Console disabled for GUI app
"""

import sys
import os
from PyInstaller.utils.hooks import get_module_file_path, collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE

# Path to spec file directory
SPECPATH = os.path.dirname(os.path.abspath(__file__))

block_cipher = None

# === HIDDEN IMPORTS ===
# Keep this minimal - PyInstaller's hooks should resolve most dependencies
hidden_imports = [
    'pywebview',
    'pywebview.api',
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtWebEngineWidgets',
    'selenium',
    'selenium.webdriver',
    'webdriver_manager',
    'requests',
    'bs4',
    'google.generativeai',
]

# === RUNTIME HOOKS ===
# Create a runtime hook to set QT_PLUGIN_PATH for PySide6
runtime_hook_code = """
import os
import sys

# Set QT_PLUGIN_PATH to the bundled PySide6 plugins
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    qt_plugins = os.path.join(base_dir, 'PySide6', 'plugins')
    if os.path.exists(qt_plugins):
        os.environ['QT_PLUGIN_PATH'] = qt_plugins
"""

runtime_hook_path = os.path.join(SPECPATH, 'runtime_hook_qt.py')
with open(runtime_hook_path, 'w') as f:
    f.write(runtime_hook_code)

# === ANALYSIS ===
a = Analysis(
    ['app_webview.py'],
    pathex=[SPECPATH],
    binaries=[],
    datas=[
        ('web', 'web'),  # Frontend assets must be included
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[runtime_hook_path],  # Use our custom runtime hook
    excludedimports=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=True,
    cipher=block_cipher,
    noarchive=False,
)

# === PYZ (Python archive) ===
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# === EXE (Executable) ===
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AcadHack',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # No console window for GUI app
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# === COLLECTION (OneDir bundle) ===
# OneDir is required for PySide6 because plugins must be in subdirectories
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AcadHack',  # Output folder name in dist/
)
