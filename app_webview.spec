# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import get_module_file_path

block_cipher = None

# Get PySide6 path for Qt plugins
try:
    pyside6_path = get_module_file_path('PySide6')
    pyside6_binaries = [
        (os.path.join(pyside6_path, 'plugins', 'platforms'), 
         os.path.join('PySide6', 'plugins', 'platforms')),
    ]
except Exception:
    pyside6_binaries = []

# Get shiboken6 path
try:
    shiboken6_path = get_module_file_path('shiboken6')
    # Some versions have DLLs in the root, some in a subfolder. 
    # We try to grab the package root.
    shiboken6_binaries = [
        (os.path.dirname(shiboken6_path), 'shiboken6')
    ]
except Exception:
    shiboken6_binaries = []

a = Analysis(
    ['app_webview.py'],
    pathex=[],
    binaries=pyside6_binaries + shiboken6_binaries,
    datas=[
        ('web', 'web'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        # PyWebView
        'webview',
        'webview.api',
        'webview.guilib',
        'webview.util',
        'webview.js',
        'webview.cache',
        'webview.platforms',
        'webview.platforms.qt',
        'webview.platforms.qt.qt',
        
        # PySide6 - Qt Core modules
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngine',
        'PySide6.QtQml',
        'PySide6.QtNetwork',
        'PySide6.QtPrintSupport',
        
        # Shiboken
        'shiboken6',
        'shiboken6.Shiboken',
        
        # Selenium & drivers
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'webdriver_manager',
        'webdriver_manager.chrome',
        'webdriver_manager.core',
        'webdriver_manager.utils',
        
        # Other dependencies
        'google.generativeai',
        'dotenv',
        'requests',
        'bs4',
        'bs4.builder',
        'urllib3',
    ],
    hookspath=[],
    hooksconfig={
        'PySide6': {
            'dynamically_detect_imports': True,
        }
    },
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'pytest',
        'setuptools',
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AcadHack',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set False after debugging
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
