"""
Enhanced security interceptor with domain allowlist and user warnings
"""

import json
import os
from typing import Set, Optional, Tuple
from urllib.parse import urlparse
from PyQt6.QtCore import QObject, pyqtSignal

from ..paths import get_app_data_dir


class DomainAllowlistManager:
    """Manages the domain allowlist with persistent storage"""
    
    def __init__(self):
        self.allowlist_file = get_app_data_dir() / "domain_allowlist.json"
        self.allowed_domains: Set[str] = set()
        self.load_allowlist()
        self._ensure_default_domains()
    
    def _ensure_default_domains(self):
        """Ensure default domains are always in the allowlist"""
        default_domains = {
            'chatgpt.com',
            'openai.com',
            'auth0.openai.com',
            'cdn.openai.com', 
            'static.openai.com',
            'api.openai.com',
            'accounts.google.com',  # For Google OAuth
            'googleapis.com',       # For Google services
            'gstatic.com',         # For Google static assets
            'fonts.googleapis.com', # For Google fonts
            'fonts.gstatic.com',   # For Google fonts
            'sentry.io',           # If error reporting is used
            'cloudflare.com',      # CDN that ChatGPT might use
            'azureedge.net',       # Azure CDN that OpenAI uses
        }
        
        changed = False
        for domain in default_domains:
            if domain not in self.allowed_domains:
                self.allowed_domains.add(domain)
                changed = True
        
        if changed:
            self.save_allowlist()
    
    def load_allowlist(self):
        """Load allowlist from disk"""
        try:
            if self.allowlist_file.exists():
                with open(self.allowlist_file, 'r') as f:
                    data = json.load(f)
                    self.allowed_domains = set(data.get('domains', []))
        except Exception:
            # If loading fails, start with empty allowlist
            self.allowed_domains = set()
    
    def save_allowlist(self):
        """Save allowlist to disk"""
        try:
            self.allowlist_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.allowlist_file, 'w') as f:
                json.dump({'domains': list(self.allowed_domains)}, f, indent=2)
        except Exception:
            # If saving fails, continue silently
            pass
    
    def add_domain(self, domain: str):
        """Add a domain to the allowlist"""
        domain = domain.lower().strip()
        if domain and domain not in self.allowed_domains:
            self.allowed_domains.add(domain)
            self.save_allowlist()
    
    def is_domain_allowed(self, url: str) -> bool:
        """
        Check if a domain is allowed (including subdomains)
        
        Args:
            url: The URL to check
            
        Returns:
            True if domain is allowed
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
            
            # Check exact match first
            if domain in self.allowed_domains:
                return True
            
            # Check if it's a subdomain of an allowed domain
            for allowed_domain in self.allowed_domains:
                if domain.endswith('.' + allowed_domain):
                    return True
            
            return False
            
        except Exception:
            return False


class SecurityInterceptor(QObject):
    """Enhanced security interceptor with domain allowlist and warnings"""
    
    # Signal emitted when user needs to make a decision about a blocked domain
    domain_decision_needed = pyqtSignal(str, str)  # url, domain
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Domain allowlist manager
        self.allowlist_manager = DomainAllowlistManager()
        
        # Use positive allowlist for schemes (more secure)
        self.allowed_schemes: Set[str] = {
            'http',
            'https',
            'about'  # We'll handle about:blank specially
        }
        
        # Track temporary one-time allowances for this session
        self.session_allowed_domains: Set[str] = set()
    
    def should_block_url(self, url: str) -> Tuple[bool, str]:
        """
        Check if URL should be blocked
        
        Args:
            url: The URL to check
            
        Returns:
            (should_block, reason) - reason is empty if not blocked
        """
        if not url:
            return True, "Empty URL"
            
        try:
            # Check schemes with positive allowlist (more secure)
            if ':' in url:
                scheme = url.split(':', 1)[0].lower().strip()
                
                if scheme not in self.allowed_schemes:
                    return True, f"Scheme '{scheme}' not allowed"
                
                # Special case: only allow about:blank, block other about: pages
                if scheme == 'about':
                    if not url.lower().strip().startswith('about:blank'):
                        return True, "Internal pages blocked for security"
            
            # Check domain allowlist
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
            
            # Allow if domain is permanently allowed
            if self.allowlist_manager.is_domain_allowed(url):
                return False, ""
            
            # Allow if domain is temporarily allowed for this session
            for session_domain in self.session_allowed_domains:
                if domain == session_domain or domain.endswith('.' + session_domain):
                    return False, ""
            
            # Block unknown domain (will trigger warning)
            return True, f"Domain '{domain}' not in allowlist"
                
        except Exception as e:
            # If URL parsing fails, block it
            return True, f"Invalid URL format: {str(e)}"
    
    def add_domain_to_allowlist(self, domain: str):
        """Add domain to permanent allowlist"""
        self.allowlist_manager.add_domain(domain)
    
    def allow_domain_once(self, domain: str):
        """Allow domain for this session only"""
        domain = domain.lower().strip()
        if domain:
            self.session_allowed_domains.add(domain)
    
    def get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
            return domain
        except Exception:
            return ""