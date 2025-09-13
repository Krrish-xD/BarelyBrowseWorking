"""
Minimal security interceptor for blocking dangerous URL schemes
"""

from typing import Set
from PyQt6.QtCore import QObject


class SecurityInterceptor(QObject):
    """Lightweight security interceptor that blocks only dangerous schemes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Only block the most dangerous schemes
        self.blocked_schemes: Set[str] = {
            'file',        # Local file access
            'data',        # Data URIs can contain malicious content  
            'javascript',  # JavaScript execution
            'vbscript',    # VBScript execution (older browsers)
            'about'        # about: pages
        }
    
    def should_block_url(self, url: str) -> bool:
        """
        Check if URL should be blocked based on scheme
        
        Args:
            url: The URL to check
            
        Returns:
            True if URL should be blocked
        """
        if not url:
            return False
            
        try:
            # Extract scheme (everything before the first ':')
            if ':' in url:
                scheme = url.split(':', 1)[0].lower().strip()
                
                # Special case: allow about:blank but block other about: schemes
                if scheme == 'about':
                    return not url.lower().strip().startswith('about:blank')
                
                return scheme in self.blocked_schemes
                
        except Exception:
            # If URL parsing fails, don't block (be permissive)
            pass
            
        return False
    
    def get_block_reason(self, url: str) -> str:
        """
        Get human-readable reason why URL was blocked
        
        Args:
            url: The blocked URL
            
        Returns:
            Reason for blocking
        """
        if not url or ':' not in url:
            return "Invalid URL format"
            
        try:
            scheme = url.split(':', 1)[0].lower().strip()
            
            if scheme == 'file':
                return "File access blocked for security"
            elif scheme == 'data':
                return "Data URIs blocked for security" 
            elif scheme == 'javascript':
                return "JavaScript execution blocked"
            elif scheme == 'vbscript':
                return "Script execution blocked"
            elif scheme == 'about':
                if url.lower().strip().startswith('about:blank'):
                    return "about:blank allowed but should not reach here"
                return "Internal pages blocked"
            else:
                return f"Scheme '{scheme}' blocked for security"
                
        except Exception:
            return "URL blocked for security"