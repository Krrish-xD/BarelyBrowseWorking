"""
Configuration constants for ChatGPT Browser
"""

# Application constants
APP_NAME = "ChatGPT Browser"
APP_ORG = "ChatGPT Browser"
CHATGPT_URL = "https://chatgpt.com"
NUM_WORKSPACES = 4
AUTOSAVE_INTERVAL_MS = 10 * 60 * 1000  # 10 minutes in milliseconds (reduced SSD wear)
NOTEPAD_SAVE_DEBOUNCE_MS = 2 * 1000  # 2 second debounce for notepad saves

# UI Constants
COLORS = {
    'primary_bg': '#141414',
    'secondary_bg': '#282828', 
    'accent': '#3c3c3c',
    'text': '#ffffff',
    'text_dim': '#cccccc'
}

# Default workspace names
DEFAULT_WORKSPACE_NAMES = [f"Workspace {i+1}" for i in range(NUM_WORKSPACES)]

# File names
SESSION_FILE = "sessions.json"
NOTEPAD_DIR = "notepads"
ASSETS_DIR = "assets"