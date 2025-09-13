"""
Web workspace management with isolated QtWebEngine profiles
"""

import os
from typing import List, Optional
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage

from ..config import CHATGPT_URL
from ..paths import get_workspace_profile_dir
from ..storage.session_manager import TabData, WorkspaceData
from .url_filter import ChatGPTUrlFilter


class ChatGPTWebView(QWebEngineView):
    """Custom web view for ChatGPT with isolated profile"""
    
    def __init__(self, workspace_id: int, profile: QWebEngineProfile, parent=None):
        super().__init__(parent)
        
        self.workspace_id = workspace_id
        
        # Use shared profile for this workspace
        self.profile = profile
        
        # Create page with shared workspace profile
        self.page_obj = QWebEnginePage(self.profile, self)
        self.setPage(self.page_obj)
        
        # Configure for secure operation
        self._setup_security_settings()
        
        # Load ChatGPT
        self.load(QUrl(CHATGPT_URL))
    
    def _setup_security_settings(self):
        """Setup security settings for the web engine"""
        # Note: In production builds, we should NOT disable the sandbox
        # This is only for development/CI environments
        if os.environ.get("QTWEBENGINE_DISABLE_SANDBOX") == "1":
            # Only in headless CI environments
            pass
        
        # Set user agent to avoid any potential blocking
        page = self.page()
        if page:
            profile = page.profile()
            if profile:
                # Use a standard Chrome user agent
                user_agent = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                )
                profile.setHttpUserAgent(user_agent)
    
    def closeEvent(self, a0):
        """Clean up resources when closing"""
        if hasattr(self, 'page_obj'):
            self.page_obj.deleteLater()
        super().closeEvent(a0)


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
        from ..config import COLORS
        
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


class WorkspaceWidget(QWidget):
    """Widget representing a single workspace with tabs"""
    
    session_changed = pyqtSignal()
    
    def __init__(self, workspace_id: int, workspace_data: WorkspaceData, parent=None):
        super().__init__(parent)
        self.workspace_id = workspace_id
        self.workspace_data = workspace_data
        self.web_views: List[ChatGPTWebView] = []
        self.closed_tabs: List[TabData] = []  # For tab restoration
        
        # Create single shared profile for this workspace
        self.workspace_profile = self._create_workspace_profile()
        
        self.setup_ui()
        self.restore_session()
    
    def _create_workspace_profile(self) -> QWebEngineProfile:
        """Create a single shared profile for this workspace"""
        profile_dir = get_workspace_profile_dir(self.workspace_id)
        profile_name = f"workspace_{self.workspace_id}"
        
        # Create profile with persistent storage
        profile = QWebEngineProfile(profile_name, self)
        profile.setPersistentStoragePath(str(profile_dir))
        profile.setCachePath(str(profile_dir / "cache"))
        
        # Enable persistent cookies and storage
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )
        
        # Configure profile settings for optimal ChatGPT experience
        settings = profile.settings()
        if settings:
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        
        # Install URL filter to restrict to ChatGPT domains only
        url_filter = ChatGPTUrlFilter(self)
        profile.setUrlRequestInterceptor(url_filter)
        
        return profile
    
    def setup_ui(self):
        """Setup the workspace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget for web views
        self.tab_widget = WorkspaceTabWidget()
        self.tab_widget.tab_close_requested.connect(self.close_tab)
        self.tab_widget.new_tab_requested.connect(self.new_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        layout.addWidget(self.tab_widget)
    
    def restore_session(self):
        """Restore tabs from workspace data"""
        for tab_data in self.workspace_data.tabs:
            self.add_tab(tab_data.url)
        
        # Set active tab
        if 0 <= self.workspace_data.active_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(self.workspace_data.active_tab)
    
    def add_tab(self, url: str = CHATGPT_URL) -> int:
        """Add a new tab with ChatGPT"""
        web_view = ChatGPTWebView(self.workspace_id, self.workspace_profile)
        web_view.load(QUrl(url))
        
        self.web_views.append(web_view)
        tab_index = self.tab_widget.addTab(web_view, "ChatGPT")
        
        # Connect signals
        web_view.titleChanged.connect(
            lambda title, idx=tab_index: self._update_tab_title(idx, title)
        )
        
        self.session_changed.emit()
        return tab_index
    
    def _update_tab_title(self, index: int, title: str):
        """Update tab title, truncating if too long"""
        if index < self.tab_widget.count():
            truncated_title = title[:30] + "..." if len(title) > 30 else title
            self.tab_widget.setTabText(index, truncated_title)
    
    def close_tab(self, index: int):
        """Close a tab and save for restoration"""
        if self.tab_widget.count() <= 1:
            return  # Don't close the last tab
        
        web_view = self.tab_widget.widget(index)
        if isinstance(web_view, ChatGPTWebView):
            # Save tab data for restoration
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
            notepad_content=self.workspace_data.notepad_content,
            notepad_visible=self.workspace_data.notepad_visible
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
    
    def cleanup(self):
        """Clean up resources"""
        for web_view in self.web_views:
            web_view.deleteLater()
        self.web_views.clear()