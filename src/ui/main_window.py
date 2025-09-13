"""
Main application window with workspace management
"""

from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QStackedWidget, QMenu,
    QDialog, QLineEdit, QLabel, QDialogButtonBox,
    QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QFont

from ..config import COLORS, NUM_WORKSPACES, AUTOSAVE_INTERVAL_MS
from ..paths import get_assets_dir
from ..storage.session_manager import SessionManager, WorkspaceData
from ..web.workspace import WorkspaceWidget
from .notepad import NotepadWidget
# Notifications removed as requested
from .memory_manager import MemoryManager
from .animated_widgets import AnimatedStackedWidget, SplitterAnimator


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
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
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
        self.workspaces: Dict[int, WorkspaceWidget] = {}
        self.notepads: Dict[int, NotepadWidget] = {}
        self.current_workspace = 0
        
        # Initialize workspace names early to avoid initialization errors
        self.workspace_names = [f"Workspace {i+1}" for i in range(NUM_WORKSPACES)]
        
        # Change tracking flags
        self.session_dirty = False
        self.notepad_dirty = False
        
# Notification system removed as requested
        
        # Memory manager for intelligent workspace compression
        self.memory_manager = MemoryManager(self)
        self.memory_manager.workspace_needs_loading.connect(self._handle_workspace_loading)
        self.memory_manager.compress_workspace_signal.connect(self._compress_workspace)
        
        # Splitter animator for smooth notepad transitions
        self.splitter_animator = SplitterAnimator(self)
        
        # Auto-save timer
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.save_sessions)
        self.autosave_timer.start(AUTOSAVE_INTERVAL_MS)
        
        self.setup_ui()
        self.setup_shortcuts()
        self.load_sessions()
        self.setup_style()
        
        # Set initial window title with current workspace
        self.update_window_title()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("ChatGPT Browser")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set window icon
        assets_dir = get_assets_dir()
        logo_path = assets_dir / "logo.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
# Status indicator removed as requested
        
        # Create container for main content with workspace pill overlay
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main content area with workspaces (no header) - using animated version
        self.workspace_stack = AnimatedStackedWidget()
        content_layout.addWidget(self.workspace_stack)
        
        # Add workspace pill indicator (floating in top-right corner)
        self.workspace_pill = self.create_workspace_pill()
        
        layout.addWidget(content_container)
        
    def create_workspace_pill(self) -> QWidget:
        """Create the floating workspace indicator pill"""
        pill = QWidget(self)
        pill.setObjectName("workspace-pill")
        pill.setFixedHeight(32)
        pill.setMinimumWidth(120)
        pill.setMaximumWidth(200)
        
        # Create layout
        pill_layout = QHBoxLayout(pill)
        pill_layout.setContentsMargins(12, 6, 12, 6)
        pill_layout.setSpacing(8)
        
        # Workspace name label
        self.workspace_label = QLabel(self.get_current_workspace_name())
        self.workspace_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        pill_layout.addWidget(self.workspace_label)
        
        # Styling for the pill
        pill.setStyleSheet(f"""
            QWidget#workspace-pill {{
                background-color: {COLORS['secondary_bg']};
                border: 1px solid {COLORS['accent']};
                border-radius: 16px;
                color: {COLORS['text']};
            }}
            QLabel {{
                color: {COLORS['text']};
                border: none;
            }}
        """)
        
        # Make pill transparent to mouse events so it doesn't interfere
        pill.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Set initial position (will be refined in resizeEvent)
        pill.move(self.width() - pill.width() - 20 if self.width() > pill.width() + 40 else 20, 20)
        pill.show()
        pill.raise_()  # Ensure it's on top
        
        return pill
    
    def get_current_workspace_name(self) -> str:
        """Get the name of the current workspace"""
        return self.workspace_names[self.current_workspace]
    
    def update_window_title(self):
        """Update window title with current workspace name"""
        workspace_name = self.get_current_workspace_name()
        self.setWindowTitle(f"ChatGPT Browser - {workspace_name}")
        
        # Update workspace pill
        if hasattr(self, 'workspace_label'):
            self.workspace_label.setText(workspace_name)
            # Ensure pill stays on top when workspace changes
            if hasattr(self, 'workspace_pill'):
                self.workspace_pill.raise_()
    
    def resizeEvent(self, event):
        """Handle window resize to reposition workspace pill"""
        super().resizeEvent(event)
        if hasattr(self, 'workspace_pill'):
            # Reposition pill to top-right corner and raise it
            self.workspace_pill.move(self.width() - self.workspace_pill.width() - 20, 20)
            self.workspace_pill.raise_()
    
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
            # Create workspace widget
            workspace_widget = WorkspaceWidget(workspace_id, data, self.toggle_current_notepad, self)
            workspace_widget.session_changed.connect(self._mark_session_dirty)
            
            self.workspaces[workspace_id] = workspace_widget
            
            # Create notepad widget
            notepad_widget = NotepadWidget(self)
            notepad_widget.set_content(data.notepad_content)
            notepad_widget.content_changed.connect(self._mark_notepad_dirty)
            notepad_widget.close_requested.connect(lambda: self.toggle_current_notepad(False))
            self.notepads[workspace_id] = notepad_widget
            
            # Create combined widget with splitter
            from PyQt6.QtWidgets import QSplitter
            combined_widget = QWidget()
            layout = QVBoxLayout(combined_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            
            splitter = QSplitter(Qt.Orientation.Vertical)
            splitter.setObjectName("main-splitter")
            splitter.addWidget(workspace_widget)
            splitter.addWidget(notepad_widget)
            # Use proportional sizing based on initial splitter height
            initial_height = 600  # Default height during setup
            main_height = int(initial_height * 0.75)
            notepad_height = int(initial_height * 0.25)
            
            splitter.setSizes([initial_height, 0])  # Hide notepad initially
            
            if data.notepad_visible:
                splitter.setSizes([main_height, notepad_height])
                notepad_widget.show()
            else:
                notepad_widget.hide()
            
            layout.addWidget(splitter)
            self.workspace_stack.addWidget(combined_widget)
            
            # Update workspace name
            if workspace_id < len(self.workspace_names):
                self.workspace_names[workspace_id] = data.name
        
# Notifications removed - workspaces loaded silently
    
    def _mark_session_dirty(self):
        """Mark session data as dirty (needs saving)"""
        self.session_dirty = True
    
    def _mark_notepad_dirty(self):
        """Mark notepad data as dirty (needs saving)"""
        self.notepad_dirty = True
    
    
    def save_sessions(self):
        """Save current workspace sessions (optimized with change detection)"""
        # Check if we have any changes to save
        if not (self.session_dirty or self.notepad_dirty):
            # Timer-based save with no changes - skip to reduce I/O
            return
        
        workspace_data = {}
        for workspace_id in range(NUM_WORKSPACES):
            if workspace_id in self.workspaces and workspace_id in self.notepads:
                session_data = self.workspaces[workspace_id].get_session_data()
                # Update notepad content
                session_data.notepad_content = self.notepads[workspace_id].get_content()
                session_data.notepad_visible = self.notepads[workspace_id].isVisible()
                workspace_data[workspace_id] = session_data
        
        # Save to session manager
        if self.session_manager.save_sessions(workspace_data):
            # Clear change flags only after successful save
            self.session_dirty = False
            self.notepad_dirty = False
            
            # Clear notepad change flags
            for notepad in self.notepads.values():
                notepad.clear_changes_flag()
    
    def switch_workspace(self, workspace_id: int):
        """Switch to specified workspace"""
        if workspace_id == self.current_workspace or workspace_id >= NUM_WORKSPACES:
            return
        
        # Save current workspace session
        self.save_sessions()
        
        # Track workspace usage for memory management
        self.memory_manager.mark_workspace_used(workspace_id)
        
        # Also mark current tab as used
        workspace_widget = self.workspaces.get(workspace_id)
        if workspace_widget and hasattr(workspace_widget, 'tab_widget'):
            current_tab_index = workspace_widget.tab_widget.currentIndex()
            if current_tab_index >= 0:
                self.memory_manager.mark_tab_used(workspace_id, current_tab_index)
        
        # Check if workspace needs to be restored from compression
        if self.memory_manager.is_workspace_compressed(workspace_id):
            workspace_widget = self.workspaces.get(workspace_id)
            if workspace_widget:
                self.memory_manager.restore_workspace(workspace_id, workspace_widget)
        
        # Switch workspace
        self.current_workspace = workspace_id
        self.workspace_stack.setCurrentIndex(workspace_id)
        
        # Update window title to show current workspace
        self.update_window_title()
    
    def show_workspace_context_menu(self, workspace_id: int, pos):
        """Show context menu for workspace renaming - not used in minimal UI"""
        # Context menu functionality removed in minimal design
        pass
    
    def rename_workspace(self, workspace_id: int):
        """Rename a workspace"""
        current_name = self.workspace_names[workspace_id]
        dialog = WorkspaceRenameDialog(current_name, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = dialog.get_name()
            if new_name:
                self.workspace_names[workspace_id] = new_name
                if workspace_id in self.workspaces:
                    self.workspaces[workspace_id].workspace_data.name = new_name
                # Update window title if this is the current workspace
                if workspace_id == self.current_workspace:
                    self.setWindowTitle(f"ChatGPT Browser - {new_name}")
                self._mark_session_dirty()
                self.save_sessions()
    
    def get_current_workspace(self) -> Optional[WorkspaceWidget]:
        """Get the currently active workspace widget"""
        return self.workspaces.get(self.current_workspace)
    
    def get_current_notepad(self) -> Optional[NotepadWidget]:
        """Get the currently active notepad widget"""
        return self.notepads.get(self.current_workspace)
    
    def _handle_workspace_loading(self, workspace_id: int):
        """Handle workspace loading when switching to a compressed workspace"""
        workspace_widget = self.workspaces.get(workspace_id)
        if workspace_widget and self.memory_manager.is_workspace_compressed(workspace_id):
            self.memory_manager.restore_workspace(workspace_id, workspace_widget)
    
    def _compress_workspace(self, workspace_id: int):
        """Compress an unused workspace to save memory"""
        if workspace_id == self.current_workspace:
            # Don't compress the currently active workspace
            return
            
        workspace_widget = self.workspaces.get(workspace_id)
        if workspace_widget:
            self.memory_manager.compress_workspace(workspace_id, workspace_widget)
    
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
    
    def toggle_current_notepad(self, show: Optional[bool] = None):
        """Toggle notepad for current workspace with smooth animation"""
        notepad = self.get_current_notepad()
        if notepad:
            # Get the splitter from the current workspace
            current_widget = self.workspace_stack.currentWidget()
            if current_widget:
                splitter = current_widget.findChild(QSplitter, "main-splitter")
                if splitter:
                    if show is None:
                        show = not notepad.isVisible()
                    
                    # Calculate proportional sizes based on splitter height
                    total_height = splitter.height() if splitter.height() > 0 else 800
                    main_height = int(total_height * 0.75)  # 75% for main area
                    notepad_height = int(total_height * 0.25)  # 25% for notepad
                    
                    if show:
                        notepad.show()
                        # Animate to show notepad with proportional sizing
                        self.splitter_animator.animate_to_sizes(splitter, [main_height, notepad_height])
                    else:
                        # Animate to hide notepad, with one-time callback
                        def hide_after_animation():
                            notepad.hide()
                            # Disconnect this specific callback
                            self.splitter_animator.animation_finished.disconnect(hide_after_animation)
                        
                        self.splitter_animator.animation_finished.connect(hide_after_animation)
                        self.splitter_animator.animate_to_sizes(splitter, [total_height, 0])
                    
                    self._mark_session_dirty()
                    self.save_sessions()
    
    def closeEvent(self, a0):
        """Handle application close event"""
        # Force immediate save of any pending notepad changes
        self._force_save_pending_changes()
        
        # Save sessions before closing
        self.save_sessions()
        
        # Clean up resources
        for workspace in self.workspaces.values():
            workspace.cleanup()
        
        if a0:
            a0.accept()
    
    def _force_save_pending_changes(self):
        """Force immediate save of any pending notepad changes that haven't triggered dirty flags yet"""
        # Check each notepad for unsaved changes and stop any pending debounce timers
        for notepad in self.notepads.values():
            # Stop any pending debounce timers to prevent them from firing after we've saved
            if hasattr(notepad, '_save_timer') and notepad._save_timer.isActive():
                notepad._save_timer.stop()
            
            # If notepad has changes that haven't been marked dirty yet, mark them now
            if notepad.has_changes():
                self.notepad_dirty = True
                # Force the content_changed signal to fire immediately
                notepad._emit_content_changed()