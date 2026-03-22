# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_all, copy_metadata
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

tkinter_datas = collect_data_files('tkinter')

datas = [
    ('assets/icon.ico', '.'),
    ('user_manual.py', '.'),
    ('browser_manager.py', '.'),
    ('launch_browser_script.py', '.'),
    ('license_manager.py', '.'),
    ('activation_dialog.py', '.'),
    ('secure_strings.py', '.'),
    ('key_generator.py', '.'),
    ('error_dialog.py', '.'),
    ('manual_data.py', '.'),
    ('core_downloader.py', '.'),
    ('playwright_downloader.py', '.'),
    ('gui.py', '.'),
    ('config.json', '.'),
] + tkinter_datas

binaries = []

hiddenimports = [
    'webview',
    'webview.platforms.edgechromium',
    'webview.platforms.winforms',
    'certifi',
    'playwright',
    'playwright.sync_api',
    'playwright._impl',
    'playwright._impl._browser',
    'playwright._impl._page',
    'playwright._impl._browser_context',
    'bs4',
    'bs4.builder',
    'PIL',
    'PIL.Image',
    'requests',
    'fake_useragent',
    'pyperclip',
    'lxml',
    'lxml.etree',
    'lxml._elementpath',
    'chardet',
    'charset_normalizer',
    'idna',
    'urllib3',
    'multiprocessing',
    'multiprocessing.spawn',
    'json',
    'traceback',
    'platform',
    'subprocess',
    'shutil',
    'concurrent.futures',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.scrolledtext',
    'tkinter.messagebox',
    'tkinter.font',
    'license_manager',
    'activation_dialog',
    'secure_strings',
    'key_generator',
    'error_dialog',
    'manual_data',
    'core_downloader',
    'playwright_downloader',
    'gui',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['test', 'tests'],
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
    name='离线网页下载器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='离线网页下载器',
)
