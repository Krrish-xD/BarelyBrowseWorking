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
    
# OAuth notifications removed
    
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
        
        For ChatGPT/OpenAI authentication flows, we keep Google OAuth within the app
        to maintain session continuity. This prevents the "invalid session" error
        that occurs when OAuth callbacks try to return to a different browser context.
        
        Args:
            url: The URL to check
            
        Returns:
            True if URL should be redirected to system browser
        """
        # IMPORTANT: For this ChatGPT Browser app, we disable OAuth redirection
        # to system browser entirely. This ensures that Google OAuth flows for
        # ChatGPT/OpenAI authentication stay within the same browser context,
        # preventing session mismatch errors.
        #
        # The original OAuth redirection was causing "Route Error (400 Invalid Session)"
        # because the OAuth session was initiated in the embedded WebView but
        # callbacks were landing in the external system browser, breaking the flow.
        
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
                return True
            else:
                # Fallback to Python webbrowser module
                webbrowser.open(url, new=2)  # new=2 opens in new tab
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