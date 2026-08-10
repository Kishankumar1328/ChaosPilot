import time
import socket
import logging
from typing import Optional
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class TargetHealth(BaseModel):
    reachable: bool
    status_code: int = 0
    final_url: str = ""
    dom_available: bool = False
    navigation_duration_ms: float = 0.0
    error_kind: Optional[str] = None  # SUCCESS, DNS_FAILURE, TARGET_UNREACHABLE, TLS_FAILURE, HTTP_ERROR, TIMEOUT

class TargetPreflight:
    """
    Executes a preflight check on target applications before testing.
    Verifies URL format, DNS resolution, TCP connectivity, HTTP response, and DOM availability.
    """
    @staticmethod
    async def check_health(target_url: str, page: Optional[Page] = None, timeout_seconds: float = 10.0) -> TargetHealth:
        start_time = time.time()
        parsed = urlparse(target_url)

        if not parsed.scheme or not parsed.hostname:
            return TargetHealth(
                reachable=False,
                error_kind="INVALID_URL_FORMAT",
                navigation_duration_ms=(time.time() - start_time) * 1000
            )

        hostname = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        # 1. DNS Resolution Check
        try:
            addresses = socket.getaddrinfo(hostname, port)
            if not addresses:
                return TargetHealth(
                    reachable=False,
                    error_kind="DNS_FAILURE",
                    navigation_duration_ms=(time.time() - start_time) * 1000
                )
        except Exception as e:
            logger.warning(f"DNS Resolution failed for {hostname}: {e}")
            return TargetHealth(
                reachable=False,
                error_kind="DNS_FAILURE",
                navigation_duration_ms=(time.time() - start_time) * 1000
            )

        # 2. HTTP / TCP Probe Check via httpx
        try:
            async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=timeout_seconds) as client:
                res = await client.get(target_url)
                status_code = res.status_code
                final_url = str(res.url)
        except httpx.ConnectTimeout:
            return TargetHealth(
                reachable=False,
                error_kind="TARGET_UNREACHABLE",
                navigation_duration_ms=(time.time() - start_time) * 1000
            )
        except httpx.ConnectError:
            return TargetHealth(
                reachable=False,
                error_kind="TARGET_UNREACHABLE",
                navigation_duration_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.warning(f"HTTP Probe check failed for {target_url}: {e}")
            return TargetHealth(
                reachable=False,
                error_kind="HTTP_PROBE_FAILED",
                navigation_duration_ms=(time.time() - start_time) * 1000
            )

        # 3. DOM Availability Verification via Playwright (if page provided)
        dom_available = True
        if page:
            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=10000)
                dom_content = await page.content()
                dom_available = len(dom_content) > 50
            except Exception as e:
                logger.warning(f"DOM availability check note for {target_url}: {e}")
                dom_available = False

        duration = (time.time() - start_time) * 1000
        return TargetHealth(
            reachable=True,
            status_code=status_code,
            final_url=final_url,
            dom_available=dom_available,
            navigation_duration_ms=duration,
            error_kind="SUCCESS"
        )
