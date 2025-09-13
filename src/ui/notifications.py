"""
Simple notification system for user feedback
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, Qt
from PyQt6.QtGui import QFont, QColor
from ..config import COLORS


class NotificationWidget(QWidget):
    """Simple notification widget that slides in and auto-hides"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(350, 60)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._opacity = 0.0
        
        self.setup_ui()
        self.setup_style()
        self.setup_animation()
        
        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_notification)
    
    def setup_ui(self):
        """Setup notification UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        self.message_label = QLabel()
        self.message_label.setFont(QFont("Arial", 10))
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
    
    def setup_style(self):
        """Apply notification styling"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['secondary_bg']};
                border: 1px solid {COLORS['accent']};
                border-radius: 8px;
            }}
            QLabel {{
                color: {COLORS['text']};
                border: none;
                background: transparent;
            }}
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
    
    def setup_animation(self):
        """Setup fade in/out animation"""
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)
    
    opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def show_notification(self, message: str, duration: int = 3000):
        """Show notification with message"""
        self.message_label.setText(message)
        
        # Position at top-right of parent
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.width() - self.width() - 20
            y = 20
            self.move(x, y)
        
        # Animate fade in
        self.show()
        try:
            self.animation.finished.disconnect()  # Clear any previous connections
        except TypeError:
            pass  # No connections to disconnect
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(0.9)
        self.animation.start()
        
        # Set auto-hide timer
        self.hide_timer.stop()
        self.hide_timer.start(duration)
    
    def hide_notification(self):
        """Hide notification with fade out"""
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass  # No connections to disconnect
        self.animation.finished.connect(self.hide)
        self.animation.setStartValue(self.get_opacity())
        self.animation.setEndValue(0.0)
        self.animation.start()


class StatusIndicator(QWidget):
    """Simple status indicator for startup progress"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        """Setup status indicator UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel("Initializing...")
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
    
    def setup_style(self):
        """Apply status indicator styling"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['primary_bg']};
                border-bottom: 1px solid {COLORS['accent']};
            }}
            QLabel {{
                color: {COLORS['text_dim']};
                border: none;
                background: transparent;
            }}
        """)
    
    def set_status(self, status: str):
        """Update status message"""
        self.status_label.setText(status)
    
    def hide_status(self):
        """Hide status indicator"""
        self.hide()