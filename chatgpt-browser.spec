# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Application info
app_name = "ChatGPTBrowser"
main_script = "main.py"

# Paths
src_path = Path("src")
assets_path = Path("assets")

# Collect data files
datas = []

# Add assets
if assets_path.exists():
    datas.append((str(assets_path), "assets"))

# Add source modules (needed for the src imports)
datas.append((str(src_path), "src"))

# Explicitly collect QtWebEngine data files and resources
try:
    # Collect QtWebEngineCore data files
    webengine_datas, webengine_binaries, webengine_hiddenimports = collect_all('PyQt6.QtWebEngineCore')
    datas.extend(webengine_datas)
    
    # Collect QtWebEngineWidgets data files  
    webwidgets_datas, webwidgets_binaries, webwidgets_hiddenimports = collect_all('PyQt6.QtWebEngineWidgets')
    datas.extend(webwidgets_datas)
    
    print(f"Collected {len(webengine_datas)} QtWebEngineCore data files")
    print(f"Collected {len(webwidgets_datas)} QtWebEngineWidgets data files")
    
except Exception as e:
    print(f"Warning: Could not auto-collect QtWebEngine data: {e}")
    webengine_binaries = []
    webengine_hiddenimports = []
    webwidgets_binaries = []
    webwidgets_hiddenimports = []

# Hidden imports for PyQt6 and WebEngine
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets',
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebEngineCore',
    'PyQt6.sip',
    'json',
    'pathlib',
    'time',
    'datetime',
    'dataclasses',
] + webengine_hiddenimports + webwidgets_hiddenimports

# Binaries - include QtWebEngine components
binaries = webengine_binaries + webwidgets_binaries

# Analysis
a = Analysis(
    [main_script],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib', 
        'PIL',
        'numpy',
        'scipy',
        'pandas'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable (onedir for QtWebEngine reliability)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed app for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets_path / "logo.png") if (assets_path / "logo.png").exists() else None,
)

# Create distribution folder (onedir for QtWebEngine)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        'QtWebEngineProcess.exe',
        'Qt6WebEngineCore.dll',
        '*.pak',
        '*.bin',
        '*.dat'
    ],
    name=app_name,
)