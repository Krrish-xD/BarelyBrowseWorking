"""
Web workspace management with isolated QtWebEngine profiles
"""

import os
from typing import List, Optional, Callable
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage

from ..config import CHATGPT_URL
from ..paths import get_workspace_profile_dir
from ..storage.session_manager import TabData, WorkspaceData
from .oauth_handler import OAuthHandler
from .security_interceptor import SecurityInterceptor


class SecurePage(QWebEnginePage):
    """Custom QWebEnginePage that properly handles navigation with security and OAuth checks"""
    
# OAuth notifications removed
    
    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(profile, parent)
        
        # Setup security components
        self.oauth_handler = OAuthHandler(self)
        self.security_interceptor = SecurityInterceptor(self)
        
        # Flag to suppress security dialogs (for popups)
        self.suppress_security_dialogs = False
        
# OAuth notification signals removed
    
    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame: bool) -> bool:
        """Override navigation request handling with security and OAuth checks"""
        url_str = url.toString()
        
        # Check security (schemes and domains)
        should_block, reason = self.security_interceptor.should_block_url(url_str)
        
        if should_block:
            # If it's a scheme issue or dangerous scheme, block silently
            if "not allowed" in reason.lower() or any(term in reason.lower() for term in ['scheme', 'internal pages']):
                return False
            
            # If it's a domain issue and we have a main window, show warning dialog (unless suppressed)
            if "not in allowlist" in reason.lower() and is_main_frame and not self.suppress_security_dialogs:
                domain = self.security_interceptor.get_domain_from_url(url_str)
                if domain:
                    # Show warning dialog
                    from ..ui.security_dialog import DomainWarningDialog
                    dialog = DomainWarningDialog(url_str, domain, self.parent())
                    
                    if dialog.exec() == dialog.Accepted:
                        choice = dialog.get_choice()
                        if choice == dialog.ALLOW_ONCE:
                            # Allow for this session
                            self.security_interceptor.allow_domain_once(domain)
                            return True
                        elif choice == dialog.ADD_TO_ALLOWLIST:
                            # Add to permanent allowlist
                            self.security_interceptor.add_domain_to_allowlist(domain)
                            return True
                    
                    # User cancelled or dialog failed
                    return False
            else:
                # Block other types silently
                return False
        
        # Check for OAuth redirects on main frame navigation
        if is_main_frame and self.oauth_handler.handle_navigation_request(url_str):
            # OAuth handler redirected to system browser
            return False
        
        # Allow all other navigation
        return True
    
# OAuth redirect notifications removed
    
    def createWindow(self, window_type):
        """
        Override popup window creation to ensure all popups use SecurePage with same security checks.
        Critical security method - ensures OAuth popups can't bypass security.
        """
        from PyQt6.QtWebEngineCore import QWebEnginePage
        
        # Get the URL that will be loaded in the popup (if available)
        # Note: Qt doesn't always provide the target URL at createWindow time
        
        # Create a new secure page with same profile for popup
        popup_page = SecurePage(self.profile(), self.parent())
        
        # Suppress security dialogs for popups (block silently)
        popup_page.suppress_security_dialogs = True
        
# Popup OAuth notifications removed
        
        # Override the popup's acceptNavigationRequest to handle OAuth immediately
        original_accept = popup_page.acceptNavigationRequest
        
        def popup_navigation_handler(url, nav_type, is_main_frame):
            """Enhanced navigation handler for popup windows"""
            url_str = url.toString()
            
            # Check security first
            should_block, reason = self.security_interceptor.should_block_url(url_str)
            if should_block:
                # For popups, be more restrictive - don't show dialogs, just block
                popup_page.deleteLater()
                return False
            
            # For popups, check OAuth redirects immediately on ANY navigation
            # (not just main frame like in regular tabs)
            if self.oauth_handler.handle_navigation_request(url_str):
                # OAuth handler redirected to system browser
                # Close the popup since OAuth is handled externally
                popup_page.deleteLater()
                return False
            
            # Use original security checks for non-OAuth URLs
            return original_accept(url, nav_type, is_main_frame)
        
        # Replace the navigation handler
        popup_page.acceptNavigationRequest = popup_navigation_handler
        
        return popup_page


class ChatGPTWebView(QWebEngineView):
    """Custom web view for ChatGPT with isolated profile"""
    
# OAuth notifications removed
    
    def __init__(self, workspace_id: int, profile: QWebEngineProfile, parent=None):
        super().__init__(parent)
        
        self.workspace_id = workspace_id
        
        # Use shared profile for this workspace
        self.profile = profile
        
        # Create secure page with shared workspace profile
        self.page_obj = SecurePage(self.profile, self)
        self.setPage(self.page_obj)
        
        # Connect security signals from the secure page
# OAuth notification connection removed
        
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
        
        # Block permissions permanently as requested by user
        settings = self.page().settings()
        
        # Disable plugins
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        
        # Block mixed content
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, False)
        
        # Connect permission requests to permanently deny them
        profile = self.page().profile()
        profile.downloadRequested.connect(self._block_download)
        
        # Override permission requests
        self.page().featurePermissionRequested.connect(self._handle_permission_request)
    
    def _block_download(self, download):
        """Block all downloads permanently"""
        download.cancel()
    
    def _handle_permission_request(self, url, feature):
        """Handle permission requests - deny all as requested"""
        from PyQt6.QtWebEngineCore import QWebEnginePage
        
        # Always deny all permission requests
        self.page().setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)
        
        # Use default user agent for better compatibility
    
    def closeEvent(self, a0):
        """Clean up resources when closing"""
        # Clean up page resources
        if hasattr(self, 'page_obj') and self.page_obj:
            self.page_obj.deleteLater()
        
        # Clear any cached URL history to free memory
        history = self.history()
        if history:
            history.clear()
        super().closeEvent(a0)


class WorkspaceTabWidget(QTabWidget):
    """Custom tab widget for individual workspace tabs"""
    
    tab_close_requested = pyqtSignal(int)
    new_tab_requested = pyqtSignal()
    
    def __init__(self, workspace_name: str = "", notepad_toggle_callback: Optional[Callable] = None, parent=None):
        super().__init__(parent)
        self.setTabsClosable(False)  # Remove close buttons as requested
        self.setMovable(True)
        self.setDocumentMode(True)
        
        self.workspace_name = workspace_name
        self.notepad_toggle_callback = notepad_toggle_callback
        
        self.setup_style()
        self.setup_corner_widget()
    
    def setup_style(self):
        """Apply dark theme styling to tabs"""
        from ..config import COLORS
        
        # Clean modern tab styling (30% bigger, similar to reference image)
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['accent']};
                background-color: {COLORS['primary_bg']};
                border-top: none;
            }}
            QTabBar::tab {{
                background-color: {COLORS['secondary_bg']};
                color: {COLORS['text']};
                padding: 10px 20px;  /* 30% bigger padding */
                margin-right: 1px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 160px;  /* 30% bigger minimum width */
                max-width: 240px;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 11px;
                font-weight: 500;
                border: 1px solid transparent;
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary_bg']};
                border: 1px solid {COLORS['accent']};
                border-bottom: 1px solid {COLORS['primary_bg']};
                color: {COLORS['text']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['accent']};
                border: 1px solid {COLORS['accent']};
                border-bottom: none;
            }}
            QTabBar {{
                qproperty-drawBase: 0;  /* Clean connection between tabs and pane */
            }}
        """)
    
    def setup_corner_widget(self):
        """Setup corner widget with workspace name and notepad toggle"""
        if not self.workspace_name:
            return
            
        corner_widget = QFrame()
        corner_widget.setObjectName("workspace-corner-widget")
        
        layout = QHBoxLayout(corner_widget)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)
        
        # Workspace name label
        workspace_label = QLabel(self.workspace_name)
        workspace_label.setObjectName("workspace-name")
        workspace_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(workspace_label)
        
        # Notepad toggle button
        if self.notepad_toggle_callback:
            notepad_btn = QPushButton("📝")
            notepad_btn.setObjectName("notepad-toggle")
            notepad_btn.setFixedSize(20, 20)
            notepad_btn.setToolTip("Toggle Notepad (Ctrl+Shift+K)")
            notepad_btn.clicked.connect(self.notepad_toggle_callback)
            layout.addWidget(notepad_btn)
        
        # Set as corner widget (top-right)
        self.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)
    
    def update_workspace_name(self, name: str):
        """Update the workspace name displayed in corner widget"""
        self.workspace_name = name
        corner_widget = self.cornerWidget(Qt.Corner.TopRightCorner)
        if corner_widget:
            label = corner_widget.findChild(QLabel, "workspace-name")
            if label:
                label.setText(name)


class WorkspaceWidget(QWidget):
    """Widget representing a single workspace with tabs"""
    
    session_changed = pyqtSignal()
# Notifications removed
    
    def __init__(self, workspace_id: int, workspace_data: WorkspaceData, notepad_toggle_callback: Optional[Callable] = None, parent=None):
        super().__init__(parent)
        self.workspace_id = workspace_id
        self.workspace_data = workspace_data
        self.notepad_toggle_callback = notepad_toggle_callback
        self.web_views: List[ChatGPTWebView] = []
        self.closed_tabs: List[TabData] = []  # For tab restoration
        self.max_closed_tabs = 10  # Limit memory usage from closed tabs
        
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
        
        # OAuth compatibility - allow third-party cookies
        try:
            # Only available in Qt 6.6+
            profile.setThirdPartyCookiePolicy(
                QWebEngineProfile.ThirdPartyCookiePolicy.AllowAll
            )
        except AttributeError:
            # Fallback for older Qt versions
            pass
        
        # Configure profile settings for optimal ChatGPT experience
        settings = profile.settings()
        if settings:
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)  # Disable plugins for memory efficiency
            settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
            # Security settings - restrict local content access
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
            
            # Memory optimization settings
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)  # OAuth needs popups
            settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, False)  # Disable WebGL for memory savings
            settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, False)  # Reduce GPU memory usage
        
        # Configure memory-efficient cache settings
        # Set cache size limits to prevent excessive memory/disk usage
        profile.setHttpCacheMaximumSize(50 * 1024 * 1024)  # 50MB cache limit
        
        # Set HTTP cache type for better memory management
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        
        # No URL filtering - allow all domains
        
        return profile
    
    def setup_ui(self):
        """Setup the workspace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget for web views with workspace info
        workspace_name = self.workspace_data.name if self.workspace_data else f"Workspace {self.workspace_id + 1}"
        self.tab_widget = WorkspaceTabWidget(workspace_name, self.notepad_toggle_callback)
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
        # Check if we have too many tabs (memory protection)
        if len(self.web_views) >= 15:  # Limit tabs per workspace for memory efficiency
            return self.tab_widget.currentIndex()  # Return current tab instead of failing
            
        web_view = ChatGPTWebView(self.workspace_id, self.workspace_profile)
        web_view.load(QUrl(url))
        
        self.web_views.append(web_view)
        tab_index = self.tab_widget.addTab(web_view, "ChatGPT")
        
        # Connect signals
        web_view.titleChanged.connect(
            lambda title, idx=tab_index: self._update_tab_title(idx, title)
        )
        web_view.oauth_notification_requested.connect(
            self.notification_requested.emit
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
            # Save tab data for restoration (with memory limit)
            self.closed_tabs.append(TabData(
                url=web_view.url().toString(),
                title=self.tab_widget.tabText(index)
            ))
            
            # Limit closed tabs to prevent memory leak
            if len(self.closed_tabs) > self.max_closed_tabs:
                self.closed_tabs.pop(0)  # Remove oldest closed tab
            
            # Remove from lists
            if web_view in self.web_views:
                self.web_views.remove(web_view)
            
            # Clean up web view resources
            # Note: Don't clear HTTP cache here as it's shared across workspace tabs
                
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
        # Clear closed tabs to free memory
        self.closed_tabs.clear()
        
        # Clean up web views
        for web_view in self.web_views:
            # Force cleanup of web engine resources
            if hasattr(web_view, 'page_obj') and web_view.page_obj:
                web_view.page_obj.deleteLater()
            web_view.deleteLater()
        self.web_views.clear()
        
        # Clean up profile resources
        if hasattr(self, 'workspace_profile'):
            self.workspace_profile.clearAllVisitedLinks()
            self.workspace_profile.clearHttpCache()