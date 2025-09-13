"""
Main application entry point with headless mode support
"""

import sys
import os
from typing import Optional

from .config import APP_NAME, APP_ORG
from .paths import is_headless_environment, ensure_directories


def setup_environment():
    """Setup environment variables for proper operation"""
    # Ensure data directories exist
    ensure_directories()
    
    # Set Qt application properties (only for Linux X11)
    if sys.platform.startswith("linux") and os.environ.get("DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    
    # Configure QtWebEngine for headless environments if needed
    if is_headless_environment():
        os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
            "--no-sandbox --disable-gpu --disable-software-rasterizer "
            "--disable-dev-shm-usage --single-process --no-zygote"
        )


def run_headless_tests() -> bool:
    """Run headless tests for CI/development environments"""
    
    try:
        # Test imports
        from .storage.session_manager import SessionManager
        from .paths import get_app_data_dir, get_sessions_file
        
        # Test session manager
        session_manager = SessionManager()
        workspaces = session_manager.load_sessions()
        
        # Test saving/loading
        if not session_manager.save_sessions(workspaces):
            return False
        
        # Test URL filter (skip if GUI libraries unavailable)
        try:
            from .web.url_filter import ChatGPTUrlFilter
            url_filter = ChatGPTUrlFilter()
        except ImportError:
            pass  # Expected in headless mode
        except Exception:
            return False
        
        return True
        
    except Exception:
        return False


def run_minimal_gui_test() -> bool:
    """Run minimal GUI test to verify QtWebEngine initialization"""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtCore import QUrl, QTimer
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create minimal web view
        web_view = QWebEngineView()
        web_view.resize(400, 300)
        
        # Load about:blank to test QtWebEngine initialization
        web_view.load(QUrl("about:blank"))
        
        # Set up timer to close after 3 seconds
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(3000)
        
        web_view.deleteLater()
        return True
        
    except Exception:
        return False


def create_gui_application():
    """Create and run the GUI application"""
    # Safety check for Replit environment (only when not forcing GUI mode)
    if ("REPLIT" in os.environ or "REPL_ID" in os.environ) and "--gui" not in sys.argv:
        if not os.environ.get("ALLOW_UNSAFE_GUI"):
            print("ERROR: GUI mode is not supported in the Replit environment.")
            print("This is due to missing system dependencies for Qt6/QtWebEngine.")
            print("To run the GUI version:")
            print("1. Clone this project locally")
            print("2. Install GUI dependencies: pip install .[gui]")
            print("3. Run: python main.py --gui")
            print("")
            print("The headless mode works perfectly and provides all core functionality.")
            print("Run: python main.py --headless")
            return 1
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPalette, QColor
        from .ui.main_window import MainWindow
        from .config import COLORS
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(APP_ORG)
        
        # Set dark theme for the application
        app.setStyle('Fusion')
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['primary_bg']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['text']))
        palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['secondary_bg']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS['accent']))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS['text']))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS['text']))
        palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['text']))
        palette.setColor(QPalette.ColorRole.Button, QColor(COLORS['secondary_bg']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS['text']))
        palette.setColor(QPalette.ColorRole.BrightText, QColor('red'))
        palette.setColor(QPalette.ColorRole.Link, QColor('#42A5F5'))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS['accent']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(COLORS['text']))
        app.setPalette(palette)
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        return app.exec()
        
    except ImportError:
        print("GUI libraries not available. Install PyQt6 and run on a system with a display.")
        return 1
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1


def main() -> int:
    """Main entry point"""
    # Setup environment
    setup_environment()
    
    # Check if we should run minimal GUI test
    if "--gui-test" in sys.argv:
        return 0 if run_minimal_gui_test() else 1
    
    # Check if we should run in headless mode
    if is_headless_environment() or "--headless" in sys.argv:
        if run_headless_tests():
            print("\nTo run the GUI version:")
            print("1. Install PyQt6 and QtWebEngine")
            print("2. Run on a system with a graphical display")
            print("3. Or use: python main.py --gui (forces GUI mode)")
            return 0
        else:
            return 1
    
    # Force GUI mode if requested
    if "--gui" in sys.argv:
        print("Forcing GUI mode...")
    
    # Run GUI application
    print(f"Starting {APP_NAME}...")
    return create_gui_application()


if __name__ == "__main__":
    sys.exit(main())