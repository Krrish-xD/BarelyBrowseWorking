"""
Intelligent memory management for workspaces and tabs
"""

import time
from typing import Dict, Set, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Configuration
COMPRESSION_DELAY_MINUTES = 5  # Compress after 5 minutes of inactivity
CHECK_INTERVAL_MS = 60000  # Check every minute


class MemoryManager(QObject):
    """Manages memory usage of workspaces and tabs with intelligent compression"""
    
    workspace_needs_loading = pyqtSignal(int)  # workspace_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Track usage timestamps for workspaces and tabs
        self.workspace_last_used: Dict[int, float] = {}
        self.tab_last_used: Dict[str, float] = {}  # "workspace_id:tab_index" format
        
        # Track compressed state
        self.compressed_workspaces: Set[int] = set()
        self.compressed_tabs: Set[str] = set()
        
        # Setup cleanup timer
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self._cleanup_unused_memory)
        self.cleanup_timer.start(CHECK_INTERVAL_MS)
    
    def mark_workspace_used(self, workspace_id: int):
        """Mark a workspace as recently used"""
        self.workspace_last_used[workspace_id] = time.time()
        
        # If workspace was compressed, mark it for loading
        if workspace_id in self.compressed_workspaces:
            self.compressed_workspaces.remove(workspace_id)
            self.workspace_needs_loading.emit(workspace_id)
    
    def mark_tab_used(self, workspace_id: int, tab_index: int):
        """Mark a specific tab as recently used"""
        tab_key = f"{workspace_id}:{tab_index}"
        self.tab_last_used[tab_key] = time.time()
        
        # If tab was compressed, remove from compressed set
        self.compressed_tabs.discard(tab_key)
    
    def is_workspace_compressed(self, workspace_id: int) -> bool:
        """Check if a workspace is currently compressed"""
        return workspace_id in self.compressed_workspaces
    
    def is_tab_compressed(self, workspace_id: int, tab_index: int) -> bool:
        """Check if a tab is currently compressed"""
        tab_key = f"{workspace_id}:{tab_index}"
        return tab_key in self.compressed_tabs
    
    def compress_workspace(self, workspace_id: int, workspace_widget):
        """Compress a workspace by suspending web views"""
        if workspace_id in self.compressed_workspaces:
            return
            
        # Suspend all tabs in this workspace
        tab_widget = workspace_widget.tab_widget
        for i in range(tab_widget.count()):
            web_view = tab_widget.widget(i)
            if isinstance(web_view, QWebEngineView):
                # Store the URL and clear the page to free memory
                current_url = web_view.url().toString()
                if hasattr(web_view, '_original_url'):
                    web_view._original_url = current_url
                else:
                    web_view._original_url = current_url
                
                # Navigate to about:blank to free memory
                web_view.setUrl(QUrl("about:blank"))
        
        self.compressed_workspaces.add(workspace_id)
    
    def restore_workspace(self, workspace_id: int, workspace_widget):
        """Restore a compressed workspace"""
        if workspace_id not in self.compressed_workspaces:
            return
            
        # Restore all tabs in this workspace
        tab_widget = workspace_widget.tab_widget
        for i in range(tab_widget.count()):
            web_view = tab_widget.widget(i)
            if isinstance(web_view, QWebEngineView) and hasattr(web_view, '_original_url'):
                # Restore the original URL
                web_view.setUrl(QUrl(web_view._original_url))
        
        self.compressed_workspaces.remove(workspace_id)
    
    def _cleanup_unused_memory(self):
        """Check for unused workspaces/tabs and compress them"""
        current_time = time.time()
        threshold_seconds = COMPRESSION_DELAY_MINUTES * 60
        
        # Find workspaces that haven't been used recently
        workspaces_to_compress = []
        for workspace_id, last_used in self.workspace_last_used.items():
            if current_time - last_used > threshold_seconds:
                if workspace_id not in self.compressed_workspaces:
                    workspaces_to_compress.append(workspace_id)
        
        # Emit signals for workspaces that need compression
        # The main window will handle the actual compression
        for workspace_id in workspaces_to_compress:
            self.compress_workspace_signal.emit(workspace_id)
    
    # Signal for main window to handle compression
    compress_workspace_signal = pyqtSignal(int)