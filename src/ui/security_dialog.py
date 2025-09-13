"""
Security warning dialog for domain access
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from ..config import COLORS


class DomainWarningDialog(QDialog):
    """Warning dialog for accessing non-whitelisted domains"""
    
    ALLOW_ONCE = 1
    ADD_TO_ALLOWLIST = 2 
    CANCEL = 0
    
    def __init__(self, url: str, domain: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.domain = domain
        self.result_choice = self.CANCEL
        
        self.setWindowTitle("Website Security Warning")
        self.setModal(True)
        self.setFixedSize(500, 280)
        
        self.setup_ui()
        self.setup_style()
        
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Warning icon and title
        title_layout = QHBoxLayout()
        
        # Warning title
        title_label = QLabel("⚠️ Unknown Website")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Message
        message = QLabel(
            f"You're trying to visit a website that's not on your approved list:\n\n"
            f"🌐 <b>{self.domain}</b>\n\n"
            f"This browser is designed to keep you safe by only allowing trusted websites. "
            f"What would you like to do?"
        )
        message.setWordWrap(True)
        message.setFont(QFont("Arial", 10))
        layout.addWidget(message)
        
        # URL display (truncated if too long)
        url_display = self.url
        if len(url_display) > 70:
            url_display = url_display[:67] + "..."
        
        url_label = QLabel(f"Full URL: {url_display}")
        url_label.setFont(QFont("Arial", 9))
        url_label.setStyleSheet(f"color: {COLORS['text_dim']}; padding: 5px;")
        layout.addWidget(url_label)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Cancel button
        cancel_btn = QPushButton("🚫 Cancel")
        cancel_btn.setFont(QFont("Arial", 10))
        cancel_btn.clicked.connect(lambda: self.choose_option(self.CANCEL))
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        # Allow once button
        allow_once_btn = QPushButton("👁️ Allow Once")
        allow_once_btn.setFont(QFont("Arial", 10))
        allow_once_btn.clicked.connect(lambda: self.choose_option(self.ALLOW_ONCE))
        button_layout.addWidget(allow_once_btn)
        
        # Add to allowlist button
        add_btn = QPushButton("✅ Always Allow")
        add_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        add_btn.clicked.connect(lambda: self.choose_option(self.ADD_TO_ALLOWLIST))
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
        
        # Explanation text
        explanation = QLabel(
            "• 'Cancel' - Stay on the current page\n"
            "• 'Allow Once' - Visit this time only\n"
            f"• 'Always Allow' - Add '{self.domain}' to your trusted sites"
        )
        explanation.setFont(QFont("Arial", 8))
        explanation.setStyleSheet(f"color: {COLORS['text_dim']}; padding: 5px;")
        layout.addWidget(explanation)
        
    def setup_style(self):
        """Apply dark theme styling"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['primary_bg']};
                color: {COLORS['text']};
                border: 2px solid {COLORS['accent']};
            }}
            QLabel {{
                color: {COLORS['text']};
                background: transparent;
            }}
            QPushButton {{
                background-color: {COLORS['secondary_bg']};
                border: 1px solid {COLORS['accent']};
                border-radius: 6px;
                padding: 8px 16px;
                color: {COLORS['text']};
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
                border-color: #555;
            }}
            QPushButton:pressed {{
                background-color: #222;
            }}
            QFrame {{
                color: {COLORS['accent']};
            }}
        """)
        
    def choose_option(self, choice: int):
        """Handle user choice"""
        self.result_choice = choice
        if choice == self.CANCEL:
            self.reject()
        else:
            self.accept()
    
    def get_choice(self) -> int:
        """Get the user's choice"""
        return self.result_choice