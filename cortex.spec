# -*- mode: python ; coding: utf-8 -*-
"""
Cortex Desktop Application — PyInstaller Spec File
Builds a standalone one-directory bundle for Windows, Linux, or macOS.
Run:  pyinstaller cortex.spec --noconfirm
"""
import sys
import os
import platform

block_cipher = None
os_type = platform.system()

# ─── Data files to bundle alongside the executable ───
datas = [
    ('data', 'data'),
    ('piper_engine/voices', 'piper_engine/voices'),
    ('scripts', 'scripts'),
    ('icon.png', '.'),
]

# Platform-specific piper binary
if os_type == 'Windows':
    if os.path.isdir('piper_engine/piper_windows'):
        datas.append(('piper_engine/piper_windows', 'piper_engine/piper_windows'))
elif os_type == 'Linux':
    if os.path.isdir('piper_engine/piper'):
        datas.append(('piper_engine/piper', 'piper_engine/piper'))
elif os_type == 'Darwin':
    # macOS piper binary (if available)
    if os.path.isdir('piper_engine/piper'):
        datas.append(('piper_engine/piper', 'piper_engine/piper'))

# ─── Hidden imports that PyInstaller can't detect automatically ───
hiddenimports = [
    'faster_whisper',
    'sklearn',
    'sklearn.utils._cython_blas',
    'sklearn.neighbors._typedefs',
    'sklearn.neighbors._partition_nodes',
    'sklearn.tree._utils',
    'pyaudio',
    'PyQt6',
    'PyQt6.sip',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pyttsx3',
    'pyttsx3.drivers',
    'pyttsx3.drivers.espeak',
    'pyttsx3.drivers.nsss',
    'pyttsx3.drivers.sapi5',
    'plyer',
    'plyer.platforms',
    'psutil',
    'pyperclip',
    'requests',
    'ctypes',
    'core',
    'core.engine',
    'core.speaking',
    'core.listening',
    'core.nlu',
    'core.runtime_path',
    'core.alsa_error',
    'core.engines',
    'core.engines.general',
    'core.engines.static',
    'core.engines.system',
    'core.engines.automation',
    'core.engines.application',
    'core.engines.file_manager',
    'core.engines.workspace',
    'core.ui',
    'core.ui.process',
    'core.ui.status_window',
    'core.ui.hub_window',
    'core.ui.settings_window',
    'core.ui.knowledge_window',
    'core.ui.automation_window',
    'core.ui.styles',
    'components',
    'components.system',
    'components.workspace',
]

# ─── Packages to exclude (reduce bundle size) ───
excludes = [
    'matplotlib',
    'tkinter',
    'test',
    'unittest',
    'xmlrpc',
    'setuptools',
    'distutils',
    'pip',
    'ensurepip',
]

# ─── Icon selection ───
if os_type == 'Windows' and os.path.exists('icon.ico'):
    app_icon = 'icon.ico'
elif os_type == 'Darwin' and os.path.exists('icon.icns'):
    app_icon = 'icon.icns'
else:
    app_icon = None  # Linux uses icon.png via .desktop file

# ─── Analysis ───
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Cortex',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,    # Keep console for logging; set to False for no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Cortex',
)

# macOS .app bundle (only used on macOS)
if os_type == 'Darwin':
    app = BUNDLE(
        coll,
        name='Cortex.app',
        icon=app_icon,
        bundle_identifier='com.cortex.voiceassistant',
        info_plist={
            'CFBundleName': 'Cortex',
            'CFBundleDisplayName': 'Cortex',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSMicrophoneUsageDescription': 'Cortex needs microphone access for voice commands.',
            'NSHighResolutionCapable': True,
        },
    )
