#!/usr/bin/env python3
"""
ChatGPT Browser - A minimal Python-based browser exclusively for chatgpt.com
with 4 isolated workspaces, session persistence, and built-in notepad.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTabBar, QPushButton, QLabel, QTextEdit, QSplitter,
    QFrame, QStackedWidget, QLineEdit, QDialog, QDialogButtonBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineProfile
from PyQt6.QtCore import (
    Qt, QTimer, QUrl, pyqtSignal, QThread, QObject,
    QSize, QRect, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QKeySequence, QShortcut, QFont,
    QPalette, QColor, QAction
)

import markdown


# Constants
CHATGPT_URL = "https://chatgpt.com"
DATA_DIR = Path("data")
ASSETS_DIR = Path("assets")
SESSION_FILE = DATA_DIR / "sessions.json"
NOTEPAD_DIR = DATA_DIR / "notepads"
AUTOSAVE_INTERVAL = 4 * 60 * 1000  # 4 minutes in milliseconds

# Color palette
COLORS = {
    'primary_bg': '#141414',
    'secondary_bg': '#282828',
    'accent': '#3c3c3c',
    'text': '#ffffff',
    'text_dim': '#cccccc'
}


@dataclass
class TabData:
    """Data structure for tab information"""
    url: str
    title: str = "ChatGPT"


@dataclass
class WorkspaceData:
    """Data structure for workspace information"""
    name: str
    tabs: List[TabData]
    active_tab: int = 0
    notepad_content: str = ""
    notepad_visible: bool = False


class SessionManager:
    """Handles session persistence and auto-save functionality"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.notepad_dir = NOTEPAD_DIR
        self.session_file = SESSION_FILE
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.notepad_dir.mkdir(exist_ok=True)
    
    def save_sessions(self, workspaces: Dict[int, WorkspaceData]):
        """Save workspace sessions to file"""
        session_data = {
            str(workspace_id): asdict(workspace_data)
            for workspace_id, workspace_data in workspaces.items()
        }
        
        try:
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")
    
    def load_sessions(self) -> Dict[int, WorkspaceData]:
        """Load workspace sessions from file"""
        if not self.session_file.exists():
            return self._create_default_workspaces()
        
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            workspaces = {}
            for workspace_id_str, data in session_data.items():
                workspace_id = int(workspace_id_str)
                tabs = [TabData(**tab_data) for tab_data in data['tabs']]
                workspaces[workspace_id] = WorkspaceData(
                    name=data['name'],
                    tabs=tabs,
                    active_tab=data.get('active_tab', 0),
                    notepad_content=data.get('notepad_content', ''),
                    notepad_visible=data.get('notepad_visible', False)
                )
            
            return workspaces
        
        except Exception as e:
            print(f"Error loading sessions: {e}")
            return self._create_default_workspaces()
    
    def _create_default_workspaces(self) -> Dict[int, WorkspaceData]:
        """Create default workspace configuration"""
        return {
            i: WorkspaceData(
                name=f"Workspace {i+1}",
                tabs=[TabData(url=CHATGPT_URL)],
                active_tab=0,
                notepad_content="",
                notepad_visible=False
            )
            for i in range(4)
        }


class NotepadWidget(QWidget):
    """Notepad widget with Markdown support"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_style()
        self.content_changed = False
    
    def setup_ui(self):
        """Setup the notepad UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QHBoxLayout()
        self.title_label = QLabel("Notepad")
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header.addWidget(self.title_label)
        header.addStretch()
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.hide)
        header.addWidget(self.close_btn)
        
        layout.addLayout(header)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_edit)
    
    def setup_style(self):
        """Apply dark theme styling"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['secondary_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['accent']};
                border-radius: 5px;
            }}
            QTextEdit {{
                background-color: {COLORS['primary_bg']};
                border: 1px solid {COLORS['accent']};
                border-radius: 3px;
                padding: 8px;
                font-family: 'Consolas', monospace;
            }}
            QPushButton {{
                background-color: {COLORS['accent']};
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #4c4c4c;
            }}
            QLabel {{
                border: none;
                color: {COLORS['text']};
            }}
        """)
    
    def _on_text_changed(self):
        """Mark content as changed when text is modified"""
        self.content_changed = True
    
    def set_content(self, content: str):
        """Set notepad content"""
        self.text_edit.setPlainText(content)
        self.content_changed = False
    
    def get_content(self) -> str:
        """Get notepad content"""
        return self.text_edit.toPlainText()
    
    def has_changes(self) -> bool:
        """Check if content has been modified"""
        return self.content_changed


class WorkspaceTabWidget(QTabWidget):
    """Custom tab widget for individual workspace tabs"""
    
    tab_close_requested = pyqtSignal(int)
    new_tab_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.tabCloseRequested.connect(self.tab_close_requested.emit)
        self.setup_style()
    
    def setup_style(self):
        """Apply dark theme styling to tabs"""
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['accent']};
                background-color: {COLORS['primary_bg']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['secondary_bg']};
                color: {COLORS['text']};
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 120px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary_bg']};
                border-bottom: 2px solid {COLORS['accent']};
            }}
            QTabBar::tab:hover {{
                background-color: {COLORS['accent']};
            }}
            QTabBar::close-button {{
                image: url();
                background-color: transparent;
                border-radius: 8px;
                width: 16px;
                height: 16px;
            }}
            QTabBar::close-button:hover {{
                background-color: #ff4444;
            }}
        """)


class ChatGPTWebView(QWebEngineView):
    """Custom web view for ChatGPT with isolated profile"""
    
    def __init__(self, workspace_id: int, parent=None):
        # Create isolated profile for this workspace
        profile_name = f"workspace_{workspace_id}"
        self.profile = QWebEngineProfile(profile_name)
        
        # Configure profile settings
        settings = self.profile.settings()
        if settings:
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        
        super().__init__(parent)
        
        # Create page with isolated profile
        self.page_obj = QWebEnginePage(self.profile, self)
        self.setPage(self.page_obj)
        
        self.workspace_id = workspace_id
        
        # Load ChatGPT
        self.load(QUrl(CHATGPT_URL))
    
    def closeEvent(self, a0):
        """Clean up resources when closing"""
        self.page_obj.deleteLater()
        super().closeEvent(a0)


class WorkspaceWidget(QWidget):
    """Widget representing a single workspace with tabs and notepad"""
    
    session_changed = pyqtSignal()
    
    def __init__(self, workspace_id: int, workspace_data: WorkspaceData, parent=None):
        super().__init__(parent)
        self.workspace_id = workspace_id
        self.workspace_data = workspace_data
        self.web_views = []
        self.closed_tabs = []  # For tab restoration
        
        self.setup_ui()
        self.restore_session()
    
    def setup_ui(self):
        """Setup the workspace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for main content and notepad
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Tab widget for web views
        self.tab_widget = WorkspaceTabWidget()
        self.tab_widget.tab_close_requested.connect(self.close_tab)
        self.tab_widget.new_tab_requested.connect(self.new_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Notepad
        self.notepad = NotepadWidget()
        self.notepad.hide()
        
        # Add to splitter
        self.splitter.addWidget(self.tab_widget)
        self.splitter.addWidget(self.notepad)
        self.splitter.setSizes([800, 0])  # Hide notepad initially
        
        layout.addWidget(self.splitter)
    
    def restore_session(self):
        """Restore tabs from workspace data"""
        for tab_data in self.workspace_data.tabs:
            self.add_tab(tab_data.url)
        
        # Set active tab
        if 0 <= self.workspace_data.active_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(self.workspace_data.active_tab)
        
        # Restore notepad
        self.notepad.set_content(self.workspace_data.notepad_content)
        if self.workspace_data.notepad_visible:
            self.toggle_notepad()
    
    def add_tab(self, url: str = CHATGPT_URL) -> int:
        """Add a new tab with ChatGPT"""
        web_view = ChatGPTWebView(self.workspace_id)
        web_view.load(QUrl(url))
        
        self.web_views.append(web_view)
        tab_index = self.tab_widget.addTab(web_view, "ChatGPT")
        
        # Connect signals
        web_view.titleChanged.connect(
            lambda title, idx=tab_index: self.tab_widget.setTabText(idx, title[:30] + "..." if len(title) > 30 else title)
        )
        
        self.session_changed.emit()
        return tab_index
    
    def close_tab(self, index: int):
        """Close a tab and save for restoration"""
        if self.tab_widget.count() <= 1:
            return  # Don't close the last tab
        
        web_view = self.tab_widget.widget(index)
        if web_view:
            # Save tab data for restoration
            if isinstance(web_view, ChatGPTWebView):
                self.closed_tabs.append(TabData(
                    url=web_view.url().toString(),
                    title=self.tab_widget.tabText(index)
                ))
            
            # Remove from lists
            if web_view in self.web_views:
                self.web_views.remove(web_view)
            
            # Close tab
            self.tab_widget.removeTab(index)
            web_view.deleteLater()
            
            self.session_changed.emit()
    
    def new_tab(self):
        """Create a new tab"""
        index = self.add_tab()
        self.tab_widget.setCurrentIndex(index)
    
    def restore_last_closed_tab(self):
        """Restore the most recently closed tab"""
        if self.closed_tabs:
            tab_data = self.closed_tabs.pop()
            index = self.add_tab(tab_data.url)
            self.tab_widget.setCurrentIndex(index)
    
    def toggle_notepad(self):
        """Toggle notepad visibility"""
        if self.notepad.isVisible():
            self.notepad.hide()
            self.splitter.setSizes([800, 0])
            self.workspace_data.notepad_visible = False
        else:
            self.notepad.show()
            self.splitter.setSizes([600, 200])
            self.workspace_data.notepad_visible = True
        
        self.session_changed.emit()
    
    def _on_tab_changed(self, index: int):
        """Handle tab change"""
        self.workspace_data.active_tab = index
        self.session_changed.emit()
    
    def get_session_data(self) -> WorkspaceData:
        """Get current session data for this workspace"""
        tabs = []
        for i in range(self.tab_widget.count()):
            web_view = self.tab_widget.widget(i)
            if isinstance(web_view, ChatGPTWebView):
                tabs.append(TabData(
                    url=web_view.url().toString(),
                    title=self.tab_widget.tabText(i)
                ))
        
        return WorkspaceData(
            name=self.workspace_data.name,
            tabs=tabs,
            active_tab=self.tab_widget.currentIndex(),
            notepad_content=self.notepad.get_content(),
            notepad_visible=self.notepad.isVisible()
        )
    
    def reload_current_tab(self):
        """Reload the current tab"""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, ChatGPTWebView):
            current_widget.reload()
    
    def navigate_back(self):
        """Navigate back in current tab"""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, ChatGPTWebView):
            current_widget.back()
    
    def navigate_forward(self):
        """Navigate forward in current tab"""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, ChatGPTWebView):
            current_widget.forward()


class WorkspaceRenameDialog(QDialog):
    """Dialog for renaming workspaces"""
    
    def __init__(self, current_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rename Workspace")
        self.setModal(True)
        self.setup_ui(current_name)
        self.setup_style()
    
    def setup_ui(self, current_name: str):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        self.name_edit = QLineEdit(current_name)
        self.name_edit.selectAll()
        layout.addWidget(QLabel("Workspace Name:"))
        layout.addWidget(self.name_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def setup_style(self):
        """Apply dark theme styling"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['secondary_bg']};
                color: {COLORS['text']};
            }}
            QLineEdit {{
                background-color: {COLORS['primary_bg']};
                border: 1px solid {COLORS['accent']};
                border-radius: 3px;
                padding: 5px;
                color: {COLORS['text']};
            }}
            QPushButton {{
                background-color: {COLORS['accent']};
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                color: {COLORS['text']};
            }}
            QPushButton:hover {{
                background-color: #4c4c4c;
            }}
            QLabel {{
                color: {COLORS['text']};
            }}
        """)
    
    def get_name(self) -> str:
        """Get the entered workspace name"""
        return self.name_edit.text().strip()


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.session_manager = SessionManager()
        self.workspaces = {}
        self.current_workspace = 0
        
        # Auto-save timer
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.save_sessions)
        self.autosave_timer.start(AUTOSAVE_INTERVAL)
        
        self.setup_ui()
        self.setup_shortcuts()
        self.load_sessions()
        self.setup_style()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("ChatGPT Browser")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set window icon
        if (ASSETS_DIR / "logo.png").exists():
            self.setWindowIcon(QIcon(str(ASSETS_DIR / "logo.png")))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Workspace switcher
        self.setup_workspace_switcher(layout)
        
        # Workspace container
        self.workspace_stack = QStackedWidget()
        layout.addWidget(self.workspace_stack)
    
    def setup_workspace_switcher(self, parent_layout):
        """Setup workspace switcher UI"""
        switcher_frame = QFrame()
        switcher_frame.setFixedHeight(50)
        switcher_layout = QHBoxLayout(switcher_frame)
        switcher_layout.setContentsMargins(10, 5, 10, 5)
        
        # Workspace buttons
        self.workspace_buttons = []
        for i in range(4):
            btn = QPushButton(f"Workspace {i+1}")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, workspace_id=i: self.switch_workspace(workspace_id))
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, workspace_id=i: self.show_workspace_context_menu(workspace_id, pos))
            self.workspace_buttons.append(btn)
            switcher_layout.addWidget(btn)
        
        # Set first workspace as active
        self.workspace_buttons[0].setChecked(True)
        
        switcher_layout.addStretch()
        
        # Notepad toggle button
        self.notepad_toggle_btn = QPushButton()
        if (ASSETS_DIR / "notepad.png").exists():
            self.notepad_toggle_btn.setIcon(QIcon(str(ASSETS_DIR / "notepad.png")))
        else:
            self.notepad_toggle_btn.setText("📝")
        self.notepad_toggle_btn.setFixedSize(30, 30)
        self.notepad_toggle_btn.clicked.connect(self.toggle_current_notepad)
        switcher_layout.addWidget(self.notepad_toggle_btn)
        
        parent_layout.addWidget(switcher_frame)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Tab management
        QShortcut(QKeySequence("Ctrl+T"), self, self.new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, self.restore_last_closed_tab)
        QShortcut(QKeySequence("Ctrl+Tab"), self, self.next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, self.previous_tab)
        
        # Navigation
        QShortcut(QKeySequence("Ctrl+R"), self, self.reload_current_tab)
        QShortcut(QKeySequence("Alt+Left"), self, self.navigate_back)
        QShortcut(QKeySequence("Alt+Right"), self, self.navigate_forward)
        
        # Workspace and features
        QShortcut(QKeySequence("Ctrl+Shift+K"), self, self.toggle_current_notepad)
        QShortcut(QKeySequence("Ctrl+Shift+1"), self, lambda: self.switch_workspace(0))
        QShortcut(QKeySequence("Ctrl+Shift+2"), self, lambda: self.switch_workspace(1))
        QShortcut(QKeySequence("Ctrl+Shift+3"), self, lambda: self.switch_workspace(2))
        QShortcut(QKeySequence("Ctrl+Shift+4"), self, lambda: self.switch_workspace(3))
    
    def setup_style(self):
        """Apply dark theme styling"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['primary_bg']};
                color: {COLORS['text']};
            }}
            QFrame {{
                background-color: {COLORS['secondary_bg']};
                border-bottom: 1px solid {COLORS['accent']};
            }}
            QPushButton {{
                background-color: {COLORS['secondary_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['accent']};
                border-radius: 5px;
                padding: 8px 12px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: {COLORS['accent']};
                border-color: #5c5c5c;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
            }}
            QStackedWidget {{
                background-color: {COLORS['primary_bg']};
            }}
        """)
    
    def load_sessions(self):
        """Load workspace sessions"""
        workspace_data = self.session_manager.load_sessions()
        
        for workspace_id, data in workspace_data.items():
            workspace_widget = WorkspaceWidget(workspace_id, data, self)
            workspace_widget.session_changed.connect(self.save_sessions)
            
            self.workspaces[workspace_id] = workspace_widget
            self.workspace_stack.addWidget(workspace_widget)
            
            # Update button text with workspace name
            if workspace_id < len(self.workspace_buttons):
                self.workspace_buttons[workspace_id].setText(data.name)
    
    def save_sessions(self):
        """Save current workspace sessions"""
        workspace_data = {}
        for workspace_id, workspace_widget in self.workspaces.items():
            workspace_data[workspace_id] = workspace_widget.get_session_data()
        
        self.session_manager.save_sessions(workspace_data)
    
    def switch_workspace(self, workspace_id: int):
        """Switch to specified workspace"""
        if workspace_id == self.current_workspace:
            return
        
        # Save current workspace session
        self.save_sessions()
        
        # Update buttons
        for i, btn in enumerate(self.workspace_buttons):
            btn.setChecked(i == workspace_id)
        
        # Switch workspace
        self.current_workspace = workspace_id
        self.workspace_stack.setCurrentIndex(workspace_id)
    
    def show_workspace_context_menu(self, workspace_id: int, pos):
        """Show context menu for workspace renaming"""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        rename_action = menu.addAction("Rename Workspace")
        if rename_action:
            rename_action.triggered.connect(lambda: self.rename_workspace(workspace_id))
        
        button = self.workspace_buttons[workspace_id]
        menu.exec(button.mapToGlobal(pos))
    
    def rename_workspace(self, workspace_id: int):
        """Rename a workspace"""
        current_name = self.workspace_buttons[workspace_id].text()
        dialog = WorkspaceRenameDialog(current_name, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = dialog.get_name()
            if new_name:
                self.workspace_buttons[workspace_id].setText(new_name)
                self.workspaces[workspace_id].workspace_data.name = new_name
                self.save_sessions()
    
    def get_current_workspace(self) -> Optional[WorkspaceWidget]:
        """Get the currently active workspace widget"""
        return self.workspaces.get(self.current_workspace)
    
    # Tab management methods
    def new_tab(self):
        """Create new tab in current workspace"""
        workspace = self.get_current_workspace()
        if workspace:
            workspace.new_tab()
    
    def close_current_tab(self):
        """Close current tab in current workspace"""
        workspace = self.get_current_workspace()
        if workspace:
            current_index = workspace.tab_widget.currentIndex()
            workspace.close_tab(current_index)
    
    def restore_last_closed_tab(self):
        """Restore last closed tab in current workspace"""
        workspace = self.get_current_workspace()
        if workspace:
            workspace.restore_last_closed_tab()
    
    def next_tab(self):
        """Switch to next tab in current workspace"""
        workspace = self.get_current_workspace()
        if workspace:
            count = workspace.tab_widget.count()
            current = workspace.tab_widget.currentIndex()
            next_index = (current + 1) % count
            workspace.tab_widget.setCurrentIndex(next_index)
    
    def previous_tab(self):
        """Switch to previous tab in current workspace"""
        workspace = self.get_current_workspace()
        if workspace:
            count = workspace.tab_widget.count()
            current = workspace.tab_widget.currentIndex()
            prev_index = (current - 1) % count
            workspace.tab_widget.setCurrentIndex(prev_index)
    
    # Navigation methods
    def reload_current_tab(self):
        """Reload current tab"""
        workspace = self.get_current_workspace()
        if workspace:
            workspace.reload_current_tab()
    
    def navigate_back(self):
        """Navigate back in current tab"""
        workspace = self.get_current_workspace()
        if workspace:
            workspace.navigate_back()
    
    def navigate_forward(self):
        """Navigate forward in current tab"""
        workspace = self.get_current_workspace()
        if workspace:
            workspace.navigate_forward()
    
    def toggle_current_notepad(self):
        """Toggle notepad for current workspace"""
        workspace = self.get_current_workspace()
        if workspace:
            workspace.toggle_notepad()
    
    def closeEvent(self, a0):
        """Handle application close event"""
        # Save sessions before closing
        self.save_sessions()
        
        # Clean up resources
        for workspace in self.workspaces.values():
            for web_view in workspace.web_views:
                web_view.deleteLater()
        
        if a0:
            a0.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("ChatGPT Browser")
    app.setOrganizationName("ChatGPT Browser")
    
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


if __name__ == "__main__":
    sys.exit(main())