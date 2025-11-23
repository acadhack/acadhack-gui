# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app_webview.py'],
    pathex=[],
    binaries=[],
    datas=[('web', 'web'), ('icon.ico', '.')],
    hiddenimports=['PySide6', 'selenium', 'pywebview', 'engineio.async_drivers.threading', 'qtpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.Qt3DCore', 'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic', 'PySide6.Qt3DRender', 'PySide6.QtCharts',
        'PySide6.QtDataVisualization', 'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.QtNetworkAuth', 'PySide6.QtRemoteObjects', 'PySide6.QtScxml',
        'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtSql',
        'PySide6.QtStateMachine', 'PySide6.QtSvg', 'PySide6.QtSvgWidgets',
        'PySide6.QtTest', 'PySide6.QtTextToSpeech', 'PySide6.QtVirtualKeyboard',
        'PySide6.QtWebSockets', 'tkinter', 'matplotlib', 'numpy', 'pandas',
        'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtPrintSupport',
        'PySide6.QtUiTools', 'PySide6.QtXml'
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)
