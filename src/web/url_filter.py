"""
URL filtering to restrict navigation to ChatGPT domains only
"""

from PyQt6.QtCore import QObject, QUrl
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo


class ChatGPTUrlFilter(QWebEngineUrlRequestInterceptor):
    """URL filter to restrict navigation to ChatGPT domains only"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Allowed domains for ChatGPT functionality (minimal and specific)
        self.allowed_domains = {
            'chatgpt.com',
            # Complete OAuth/Auth domains for login flows
            'auth0.openai.com',
            'auth.openai.com', 
            'login.openai.com',
            'openai.auth0.com',
            # Essential OpenAI API and CDN domains
            'cdn.openai.com', 
            'static.openai.com',
            'api.openai.com',
            'files.oaiusercontent.com',
            # CRITICAL: Main ChatGPT CDN for CSS/JS resources
            'cdn.oaistatic.com',
            'oaistatic.com',
            # Specific CDN subdomains that ChatGPT actually uses
            'cdnjs.cloudflare.com',
            'chat.openai.com.cdn.cloudflare.net',
            # Required for OAuth and essential functionality
            'openaiapi-site.azureedge.net',
            'openaicomproductionae4b.blob.core.windows.net',
            # Additional voice features
            'chatgpt.livekit.cloud'
        }
        
        # Allowed URL patterns for specific resources
        self.allowed_patterns = [
            'data:',  # Data URLs for images, etc.
            'blob:',  # Blob URLs for file handling
            'about:blank',  # Blank pages
        ]
    
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        """Intercept and filter URL requests"""
        url = info.requestUrl()
        url_string = url.toString()
        
        # Allow specific URL patterns
        for pattern in self.allowed_patterns:
            if url_string.startswith(pattern):
                return
        
        # Check domain
        host = url.host().lower()
        
        # Allow main domain and subdomains
        allowed = False
        for domain in self.allowed_domains:
            if host == domain or host.endswith('.' + domain):
                allowed = True
                break
        
        # Block if not allowed
        if not allowed:
            info.block(True)
            return
        
        # Allow the request explicitly
        info.block(False)