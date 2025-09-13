"""
Notepad widget with Markdown support
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..config import COLORS


class NotepadWidget(QWidget):
    """Notepad widget with Markdown support"""
    
    content_changed = pyqtSignal()
    close_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_style()
        self._content_changed = False
    
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
        self.close_btn.clicked.connect(self.close_requested.emit)
        header.addWidget(self.close_btn)
        
        layout.addLayout(header)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.text_edit.setPlaceholderText("Write your notes here... Markdown is supported!")
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
                color: {COLORS['text']};
            }}
            QPushButton {{
                background-color: {COLORS['accent']};
                border: none;
                border-radius: 10px;
                font-weight: bold;
                color: {COLORS['text']};
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
        self._content_changed = True
        self.content_changed.emit()
    
    def set_content(self, content: str):
        """Set notepad content"""
        self.text_edit.setPlainText(content)
        self._content_changed = False
    
    def get_content(self) -> str:
        """Get notepad content"""
        return self.text_edit.toPlainText()
    
    def has_changes(self) -> bool:
        """Check if content has been modified"""
        return self._content_changed
    
    def clear_changes_flag(self):
        """Clear the changes flag (called after saving)"""
        self._content_changed = False