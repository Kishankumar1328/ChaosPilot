from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class DomainLock:
    """
    Enforces domain isolation so the agent never drifts onto external sites
    (e.g., social links, payment providers, third-party trackers).
    """
    def __init__(self, target_url: str):
        parsed = urlparse(target_url)
        self.allowed_host = parsed.hostname.lower() if parsed.hostname else ""
        self.allowed_scheme = parsed.scheme.lower() if parsed.scheme else "http"

    def is_allowed(self, url: str) -> bool:
        if not url or url.startswith("javascript:") or url.startswith("mailto:") or url.startswith("tel:"):
            return False
        
        # Handle relative URLs
        if url.startswith("/"):
            return True
            
        parsed = urlparse(url)
        if not parsed.hostname:
            return True
            
        target_host = parsed.hostname.lower()
        
        # Exact match or subdomain match
        if target_host == self.allowed_host or target_host.endswith(f".{self.allowed_host}"):
            return True
            
        logger.warning(f"DomainLock BLOCKED navigation to external host: {target_host} (Allowed: {self.allowed_host})")
        return False
