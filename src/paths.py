"""
Cross-platform path management for ChatGPT Browser
"""

import os
import sys
from pathlib import Path
from typing import Optional

def get_app_data_dir() -> Path:
    """Get the application data directory for the current platform"""
    try:
        from PyQt6.QtCore import QStandardPaths
        # Use Qt's standard paths for cross-platform compatibility
        app_data = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        if app_data:
            return Path(app_data)
    except ImportError:
        pass
    
    # Fallback to manual platform detection
    if sys.platform == "win32":
        # Windows: %APPDATA%\ChatGPT Browser
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / "ChatGPT Browser"
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/ChatGPT Browser
        home = Path.home()
        return home / "Library" / "Application Support" / "ChatGPT Browser"
    else:
        # Linux: ~/.local/share/ChatGPT Browser
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / "ChatGPT Browser"
        return Path.home() / ".local" / "share" / "ChatGPT Browser"
    
    # Ultimate fallback
    return Path.home() / ".chatgpt-browser"

def get_workspace_data_dir(workspace_id: int) -> Path:
    """Get the data directory for a specific workspace"""
    base_dir = get_app_data_dir()
    return base_dir / f"workspace_{workspace_id}"

def get_workspace_profile_dir(workspace_id: int) -> Path:
    """Get the QtWebEngine profile directory for a specific workspace"""
    return get_workspace_data_dir(workspace_id) / "profile"

def get_workspace_notepad_file(workspace_id: int) -> Path:
    """Get the notepad file path for a specific workspace"""
    return get_workspace_data_dir(workspace_id) / "notepad.md"

def get_sessions_file() -> Path:
    """Get the sessions file path"""
    return get_app_data_dir() / "sessions.json"

def ensure_directories():
    """Ensure all necessary directories exist"""
    # Create main app data directory
    get_app_data_dir().mkdir(parents=True, exist_ok=True)
    
    # Create workspace directories
    for i in range(4):  # 4 workspaces
        get_workspace_data_dir(i).mkdir(parents=True, exist_ok=True)
        get_workspace_profile_dir(i).mkdir(parents=True, exist_ok=True)

def get_assets_dir() -> Path:
    """Get the assets directory (relative to script location)"""
    # In development, assets are relative to the script
    # In packaged app, they'll be in the bundle
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        bundle_dir = Path(getattr(sys, '_MEIPASS', '.'))
        return bundle_dir / "assets"
    else:
        # Running in development
        script_dir = Path(__file__).parent.parent
        return script_dir / "assets"

def is_headless_environment() -> bool:
    """Check if we're running in a headless environment"""
    # Check for common headless indicators
    if os.environ.get("HEADLESS") == "1":
        return True
    
    # Check if DISPLAY is set on Linux
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    
    # Check for CI environment variables
    ci_indicators = ["CI", "GITHUB_ACTIONS", "TRAVIS", "JENKINS", "REPLIT"]
    if any(os.environ.get(var) for var in ci_indicators):
        return True
    
    return False