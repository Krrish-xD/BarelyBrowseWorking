"""
Animated widgets for smooth transitions
"""

from PyQt6.QtWidgets import QStackedWidget, QWidget, QGraphicsOpacityEffect, QSplitter
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer, QObject, QVariantAnimation


class AnimatedStackedWidget(QStackedWidget):
    """QStackedWidget with crossfade animation between pages"""
    
    animation_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_duration = 250  # 250ms as requested
        self.current_animation = None
        self.next_index = -1
        self.preload_timer = QTimer()
        self.preload_timer.setSingleShot(True)
        self.preload_timer.timeout.connect(self._start_animation)
        
    def setCurrentIndexAnimated(self, index: int):
        """Switch to index with crossfade animation"""
        if index == self.currentIndex() or index < 0 or index >= self.count():
            return
            
        # Store the target index
        self.next_index = index
        
        # Start preloading immediately (this gives time for workspace to load)
        self.preload_timer.start(0)  # Start immediately but allows other operations
        
    def _start_animation(self):
        """Start the crossfade animation"""
        if self.next_index == -1 or self.current_animation:
            return
            
        current_widget = self.currentWidget()
        next_widget = self.widget(self.next_index)
        
        if not current_widget or not next_widget:
            self.setCurrentIndex(self.next_index)
            self.next_index = -1
            return
        
        # Create opacity effects
        current_effect = QGraphicsOpacityEffect()
        next_effect = QGraphicsOpacityEffect()
        
        current_widget.setGraphicsEffect(current_effect)
        next_widget.setGraphicsEffect(next_effect)
        
        # Set initial opacity values
        current_effect.setOpacity(1.0)
        next_effect.setOpacity(0.0)
        
        # Make next widget visible and on top
        next_widget.show()
        next_widget.raise_()
        
        # Create animations
        self.fade_out_animation = QPropertyAnimation(current_effect, b"opacity")
        self.fade_out_animation.setDuration(self.animation_duration)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        self.fade_in_animation = QPropertyAnimation(next_effect, b"opacity")
        self.fade_in_animation.setDuration(self.animation_duration)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Connect animation finished
        self.fade_in_animation.finished.connect(self._animation_finished)
        
        # Set current animation reference
        self.current_animation = self.fade_in_animation
        
        # Start animations
        self.fade_out_animation.start()
        self.fade_in_animation.start()
        
        # Don't switch index immediately - wait for animation to complete
        
    def _animation_finished(self):
        """Clean up after animation completes"""
        if self.current_animation:
            # Now switch to the target index
            target_index = self.next_index
            super().setCurrentIndex(target_index)
            
            # Remove opacity effects from all widgets
            for i in range(self.count()):
                widget = self.widget(i)
                if widget:
                    widget.setGraphicsEffect(None)
            
            self.current_animation = None
            self.next_index = -1
            self.animation_finished.emit()
            
    def setCurrentIndex(self, index: int):
        """Override to use animated version by default"""
        if hasattr(self, 'animation_duration'):  # Check if fully initialized
            self.setCurrentIndexAnimated(index)
        else:
            super().setCurrentIndex(index)


class SplitterAnimator(QObject):
    """Handles smooth animation of QSplitter sizes"""
    
    animation_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation = None
        self.current_splitter = None
        self.start_sizes = []
        self.end_sizes = []
        
    def animate_to_sizes(self, splitter: QSplitter, target_sizes: list, duration: int = 140):
        """Animate splitter to target sizes"""
        if not splitter or self.animation:
            return
            
        # Get current sizes
        current_sizes = splitter.sizes()
        if len(current_sizes) != len(target_sizes):
            # Fallback to instant change if sizes don't match
            splitter.setSizes(target_sizes)
            self.animation_finished.emit()
            return
        
        # Store references for the animation
        self.current_splitter = splitter
        self.start_sizes = current_sizes[:]
        self.end_sizes = target_sizes[:]
        
        # Create variant animation that goes from 0 to 1
        self.animation = QVariantAnimation(self)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setDuration(duration)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Connect value change to our interpolation method
        self.animation.valueChanged.connect(self._update_splitter_sizes)
        self.animation.finished.connect(self._on_animation_finished)
        
        # Start animation
        self.animation.start()
    
    def _update_splitter_sizes(self, progress):
        """Update splitter sizes based on animation progress"""
        if not self.current_splitter:
            return
            
        # Interpolate between start and end sizes
        current_sizes = []
        for start, end in zip(self.start_sizes, self.end_sizes):
            interpolated = start + (end - start) * progress
            current_sizes.append(int(interpolated))
        
        self.current_splitter.setSizes(current_sizes)
        
    def _on_animation_finished(self):
        """Clean up after animation"""
        # Ensure final sizes are set exactly
        if self.current_splitter and self.end_sizes:
            self.current_splitter.setSizes(self.end_sizes)
            
        self.animation = None
        self.current_splitter = None
        self.start_sizes = []
        self.end_sizes = []
        self.animation_finished.emit()