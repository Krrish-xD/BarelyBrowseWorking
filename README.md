# ChatGPT Browser

A minimal Python-based desktop browser exclusively for ChatGPT.com with advanced workspace management and session persistence.

## Features

### Core Functionality
- **Dedicated ChatGPT Browser**: Exclusively displays and interacts with chatgpt.com
- **4 Isolated Workspaces**: Each with separate cookies, cache, and local storage
- **Multi-Tab Support**: Multiple ChatGPT tabs per workspace
- **Session Persistence**: Automatic saving and restoration of workspace states
- **Built-in Notepad**: Per-workspace notepad with Markdown support

### Session Management
- **Auto-save**: Sessions saved every 4 minutes
- **Save Triggers**: App close, workspace switch, tab close
- **Restore on Startup**: All workspaces and tabs restored when app starts
- **Isolated Storage**: Each workspace has completely separate data

### UI & UX
- **Dark Theme**: Modern dark interface (#141414, #282828, #3c3c3c)
- **Workspace Switching**: Quick switching between 4 workspaces
- **Tab Management**: Full tab management with restore functionality
- **Keyboard Shortcuts**: Comprehensive shortcut support

### Keyboard Shortcuts

#### Tab Management
- `Ctrl+T`: Open new tab
- `Ctrl+W`: Close current tab  
- `Ctrl+Shift+T`: Restore last closed tab
- `Ctrl+Tab`: Next tab
- `Ctrl+Shift+Tab`: Previous tab

#### Navigation
- `Ctrl+R`: Reload current tab
- `Alt+Left`: Navigate back
- `Alt+Right`: Navigate forward

#### Workspace & Features
- `Ctrl+Shift+K`: Toggle notepad
- `Ctrl+Shift+1-4`: Switch to workspace 1-4

## Installation & Usage

### Development Mode (Replit)
```bash
# Run headless tests
python main.py --headless

# Force GUI mode (requires display)
python main.py --gui
```

### Building Windows Executable

The application is designed to be built into a standalone Windows executable using GitHub Actions:

1. **Push to GitHub**: The repository will automatically build Windows executables
2. **Download**: Get the executable from GitHub Actions artifacts or releases
3. **Run**: Double-click the .exe file to run the application

#### Manual Build (Windows)
```bash
# Install dependencies
pip install PyQt6 PyQt6-WebEngine markdown pyinstaller

# Build executable
pyinstaller chatgpt-browser.spec

# Find executable in dist/ChatGPTBrowser/
```

## Architecture

### Cross-Platform Design
- **Windows**: Uses `%APPDATA%\\ChatGPT Browser` for data storage
- **macOS**: Uses `~/Library/Application Support/ChatGPT Browser`
- **Linux**: Uses `~/.local/share/ChatGPT Browser`

### Workspace Isolation
Each workspace maintains:
- Separate QtWebEngine profiles
- Independent cookies and sessions
- Isolated local storage and cache
- Individual notepad content

### Memory Efficiency
- Lazy loading of workspace resources
- Proper cleanup on tab/workspace close
- Optimized session data storage
- Minimal memory footprint

## File Structure

```
├── src/
│   ├── config.py          # Application constants
│   ├── paths.py           # Cross-platform path management
│   ├── app.py            # Main application entry point
│   ├── storage/
│   │   └── session_manager.py  # Session persistence
│   ├── web/
│   │   └── workspace.py        # Web engine & workspace logic
│   └── ui/
│       ├── main_window.py      # Main application window
│       └── notepad.py          # Notepad widget
├── assets/
│   ├── logo.png          # Application icon
│   └── notepad.png       # Notepad toggle icon
├── main.py               # Entry point
├── chatgpt-browser.spec  # PyInstaller configuration
└── .github/workflows/
    └── build-windows.yml # Windows build automation
```

## Security & Privacy

- **Isolated Profiles**: Each workspace has completely separate browser profiles
- **Local Storage**: All data stored locally, no external data transmission
- **Secure Defaults**: Standard web security policies applied
- **No Tracking**: Application doesn't collect or transmit user data

## Requirements

### Runtime
- Windows 10/11 (for executable)
- Python 3.11+ (for development)

### Development
- PyQt6
- PyQt6-WebEngine  
- markdown
- pyinstaller (for building)

## Contributing

This project is designed for personal use but contributions are welcome for:
- Bug fixes
- Performance improvements
- Cross-platform compatibility
- Additional workspace features

## License

This project is for personal use. ChatGPT and OpenAI are trademarks of their respective owners.