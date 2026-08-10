from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class DomainLock:
    """
    Enforces domain isolation so the agent never drifts onto external sites
    (e.g., social links, payment providers, third-party trackers).
    Supports www and apex domain matching seamlessly.
    """
    def __init__(self, target_url: str):
        parsed = urlparse(target_url)
        raw_host = parsed.hostname.lower() if parsed.hostname else ""
        self.allowed_host = raw_host
        self.base_domain = raw_host[4:] if raw_host.startswith("www.") else raw_host

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
        target_base = target_host[4:] if target_host.startswith("www.") else target_host
        
        # Exact match, base domain match, or subdomain match
        if (
            target_host == self.allowed_host 
            or target_base == self.base_domain 
            or target_base.endswith(f".{self.base_domain}")
            or self.base_domain.endswith(f".{target_base}")
        ):
            return True
            
        logger.warning(f"DomainLock BLOCKED navigation to external host: {target_host} (Allowed Base: {self.base_domain})")
        return False
