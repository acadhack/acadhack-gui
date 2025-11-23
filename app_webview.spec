# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PySide6 + PyWebview application
Stack: Python 3.11, PySide6, PyWebview (Qt backend), Selenium
Platform: Windows (GitHub Actions)

Key fixes applied:
1. Proper Qt plugin collection using collect()
2. Web folder added as datas (NOT binaries)
3. Runtime hook to set QT_QPA_PLATFORM_PLUGIN_PATH
4. UPX exclusion for Qt DLLs
5. Hidden imports for PySide6 and pywebview
6. Avoids __file__ issues with proper path handling
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

# Get current working directory (use this, NOT __file__)
spec_dir = os.getcwd()

# Paths for your application
app_entry_point = 'app_webview.py'
web_folder = 'web'

# Verify paths exist
if not os.path.exists(app_entry_point):
    raise FileNotFoundError(f"Entry point not found: {app_entry_point}")
if not os.path.isdir(web_folder):
    raise FileNotFoundError(f"Web folder not found: {web_folder}")

# ============================================================================
# PyInstaller Analysis Configuration
# ============================================================================

a = Analysis(
    [app_entry_point],
    pathex=[],
    binaries=[],
    datas=[
        # CRITICAL: Add web folder as data (destination must be relative path)
        (web_folder, web_folder),
        # Collect PySide6 data files (plugins, translations)
        *collect_data_files('PySide6'),
    ],
    hiddenimports=[
        # PySide6/Qt core modules
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        'PySide6.QtWebEngineWidgets',
        # PyWebview
        'pywebview',
        'pywebview.api',
        # Selenium and dependencies
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.common.keys',
        'selenium.webdriver.support',
        'webdriver_manager',
        'webdriver_manager.chrome',
        # Common dependencies that may be missed
        'pkg_resources.extern',
        'encodings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[
        # Custom runtime hook to set Qt plugin path
        'rthook_pyside6_qtplugins.py',
    ],
    excludedimports=[
        # Explicitly exclude conflicting Qt bindings
        'PyQt5',
        'PyQt6',
        'PySide2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

# ============================================================================
# Build EXE (onedir mode - better for debugging)
# ============================================================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app_webview',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        # DO NOT compress Qt platform plugin DLLs
        'qwindows.dll',
        'qwindowsvistastyle.dll',
    ],
    console=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ============================================================================
# Collect all generated files into dist directory
# ============================================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        'qwindows.dll',
        'qwindowsvistastyle.dll',
    ],
    name='app_webview',
)
