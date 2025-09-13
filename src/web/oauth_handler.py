"""
Lightweight OAuth handler for redirecting authentication to system browser
"""

import webbrowser
from typing import Optional
from urllib.parse import urlparse
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices


class OAuthHandler(QObject):
    """Minimal OAuth detection and redirection handler"""
    
    oauth_redirect_requested = pyqtSignal(str, str)  # url, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # OAuth patterns that should be redirected to system browser
        self.oauth_patterns = [
            'accounts.google.com',
            'oauth2.googleapis.com',
            'accounts.youtube.com',
            'myaccount.google.com/oauth',
            'oauth.googleusercontent.com'
        ]
    
    def should_redirect_to_system_browser(self, url: str) -> bool:
        """
        Check if URL should be redirected to system browser for OAuth
        
        Args:
            url: The URL to check
            
        Returns:
            True if URL should be redirected to system browser
        """
        try:
            parsed = urlparse(url.lower())
            hostname = parsed.netloc.lower()
            
            # Check if it's a Google OAuth URL
            for pattern in self.oauth_patterns:
                if pattern in hostname:
                    # Additional check for oauth-related paths
                    path = parsed.path.lower()
                    if any(keyword in path for keyword in ['oauth', 'auth', 'signin', 'login']):
                        return True
                    # Check for OAuth query parameters
                    if 'oauth' in parsed.query.lower() or 'response_type' in parsed.query.lower():
                        return True
                        
        except Exception:
            # If URL parsing fails, don't redirect
            pass
            
        return False
    
    def redirect_to_system_browser(self, url: str) -> bool:
        """
        Redirect OAuth URL to system browser
        
        Args:
            url: The URL to redirect
            
        Returns:
            True if redirect was successful
        """
        try:
            # Use Qt's desktop services for reliable opening
            qurl = QUrl(url)
            success = QDesktopServices.openUrl(qurl)
            
            if success:
                message = (
                    "🔒 OAuth authentication opened in your default browser "
                    "for security. Complete the sign-in there, then return here."
                )
                self.oauth_redirect_requested.emit(url, message)
                return True
            else:
                # Fallback to Python webbrowser module
                webbrowser.open(url, new=2)  # new=2 opens in new tab
                message = (
                    "🔒 OAuth authentication opened in your browser. "
                    "Complete the sign-in there, then return here."
                )
                self.oauth_redirect_requested.emit(url, message)
                return True
                
        except Exception as e:
            # If both methods fail, let the navigation continue normally
            return False
    
    def handle_navigation_request(self, url: str) -> bool:
        """
        Handle navigation request and redirect OAuth if needed
        
        Args:
            url: The requested navigation URL
            
        Returns:
            True if navigation was handled (redirected), False to continue normally
        """
        if self.should_redirect_to_system_browser(url):
            return self.redirect_to_system_browser(url)
        return False