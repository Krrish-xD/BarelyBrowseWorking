# How to Use ChatGPT Browser

This guide will help you set up, build, and run the ChatGPT Browser application on your Windows machine.

## 📋 Prerequisites

### Required Software
1. **Python 3.11 or higher**
   - Download from: https://www.python.org/downloads/
   - ⚠️ **IMPORTANT**: During installation, check "Add Python to PATH"

2. **Git** (optional, for cloning from GitHub)
   - Download from: https://git-scm.com/download/win

## 🚀 Quick Start

### Option 1: Download from Replit
1. Export your project as a ZIP file from Replit
2. Extract the ZIP file to a folder on your Windows machine
3. Open Command Prompt or PowerShell in that folder

### Option 2: Clone from GitHub (if you've pushed to GitHub)
```bash
git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name
```

## 🔧 Installing Dependencies

Open Command Prompt or PowerShell in your project folder and run:

```bash
# Install required Python packages
pip install PyQt6 PyQt6-WebEngine pyinstaller
```

If you encounter permission issues, try:
```bash
pip install --user PyQt6 PyQt6-WebEngine pyinstaller
```

## 🎮 Running the Application

### Development Mode (Python)
To run the application directly with Python:

```bash
# Run the GUI application
python main.py

# Run headless tests (no GUI)
python main.py --headless

# Force GUI mode
python main.py --gui
```

### First Run
- The application will create a data folder in `%APPDATA%\ChatGPT Browser`
- This is where your sessions, notepad content, and settings are stored
- Each workspace gets its own isolated browser profile

## 🔨 Building Windows Executable

### Build the Executable
To create a standalone Windows executable that users can run without Python:

```bash
# Clean build (recommended)
pyinstaller --clean --distpath dist --workpath build chatgpt-browser.spec
```

### Find Your Executable
After building, you'll find your executable at:
```
dist/ChatGPTBrowser/ChatGPTBrowser.exe
```

### Distribute the Application
To share with others:
1. Zip the entire `dist/ChatGPTBrowser/` folder
2. Recipients extract and run `ChatGPTBrowser.exe`
3. No Python installation required on target machines

## 🎯 Using the Application

### Workspace Management
- **4 Independent Workspaces**: Each supports different ChatGPT accounts
- **Switch Workspaces**: Use `Ctrl+Shift+1` through `Ctrl+Shift+5`
- **Rename Workspaces**: Right-click on workspace buttons

### Tab Management
- **New Tab**: `Ctrl+T`
- **Close Tab**: `Ctrl+W`
- **Restore Closed Tab**: `Ctrl+Shift+T`
- **Navigate Tabs**: `Ctrl+Tab` (next), `Ctrl+Shift+Tab` (previous)

### Navigation
- **Reload**: `Ctrl+R`
- **Back**: `Alt+Left Arrow`
- **Forward**: `Alt+Right Arrow`

### Built-in Notepad
- **Toggle Notepad**: `Ctrl+Shift+K` or click the notepad icon
- **Per-Workspace**: Each workspace has its own notepad
- **Auto-Save**: Content saves automatically when modified
- **Markdown Support**: Write notes in Markdown format

### Session Persistence
- **Auto-Save**: Sessions save every 4 minutes
- **Manual Save**: Triggered on workspace switch, tab close, app close
- **Restoration**: All workspaces and tabs restore on app startup

## 🛠️ Troubleshooting

### Common Issues

**"Python is not recognized"**
- Reinstall Python and ensure "Add to PATH" is checked
- Or add Python to your PATH manually

**"No module named PyQt6"**
- Run: `pip install PyQt6 PyQt6-WebEngine`
- If using multiple Python versions, try: `python -m pip install PyQt6 PyQt6-WebEngine`

**Executable won't start**
- Make sure you're running `ChatGPTBrowser.exe` from the `dist/ChatGPTBrowser/` folder
- Don't move the .exe file out of its folder (it needs the supporting files)

**Application crashes on startup**
- Try running from Command Prompt to see error messages:
  ```bash
  cd dist/ChatGPTBrowser
  ChatGPTBrowser.exe
  ```

**Can't access certain websites**
- The application is designed to only work with ChatGPT.com and essential OpenAI domains
- This is intentional for security and focus

### Performance Tips
- Close unused tabs to save memory
- Each workspace uses its own browser engine, so limit open workspaces if needed
- The application stores data locally in `%APPDATA%\ChatGPT Browser`

## 📁 File Structure

```
your-project/
├── src/                    # Source code
│   ├── config.py          # Application settings
│   ├── paths.py           # File path management
│   ├── app.py            # Main application logic
│   ├── storage/          # Session management
│   ├── web/              # Browser and workspace logic
│   └── ui/               # User interface
├── assets/               # Application icons
├── main.py              # Entry point
├── chatgpt-browser.spec  # Build configuration
└── HOW_TO_USE.md        # This file
```

## 🔄 Automatic Building (Advanced)

If you push this project to GitHub, the included GitHub Actions workflow will automatically:
1. Build Windows executables on every commit
2. Run tests to verify the build works
3. Create downloadable artifacts
4. Optionally create releases for tagged versions

To use this:
1. Push your code to a GitHub repository
2. The workflow runs automatically
3. Download built executables from the "Actions" tab

## 🆘 Getting Help

If you encounter issues:
1. Check this guide first
2. Try running `python main.py --headless` to test basic functionality
3. Look for error messages in Command Prompt
4. Make sure all dependencies are properly installed

## 🎉 Enjoy Your ChatGPT Browser!

You now have a dedicated desktop application for ChatGPT with:
- 4 isolated workspaces for multiple accounts
- Built-in notepad for each workspace
- Complete session persistence
- Professional keyboard shortcuts
- Secure, ChatGPT-only browsing

The application saves everything automatically and restores your exact session when you restart it.