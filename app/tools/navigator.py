import logging
from typing import Dict, List, Tuple
from playwright.async_api import Page
from app.models.sitemap import RouteNode, FormElement
from app.safety.domain_lock import DomainLock

logger = logging.getLogger(__name__)

class Navigator:
    """
    Handles page navigation, DOM exploration, form parsing,
    and Accessibility Tree (AXTree) snapshotting.
    """
    def __init__(self, page: Page, domain_lock: DomainLock):
        self.page = page
        self.domain_lock = domain_lock

    async def navigate_to(self, url: str) -> Tuple[bool, str, int]:
        if not self.domain_lock.is_allowed(url):
            return False, f"DomainLock blocked navigation to external URL: {url}", 403

        try:
            try:
                response = await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
            except Exception:
                response = await self.page.goto(url, wait_until="load", timeout=15000)

            status_code = response.status if response else 200
            title = await self.page.title()
            return True, f"Navigated to {url} (Title: {title}, Status: {status_code})", status_code
        except Exception as e:
            logger.error(f"Navigation error for {url}: {e}")
            return False, f"Navigation failed: {str(e)}", 500

    async def extract_route_node(self, depth: int) -> RouteNode:
        current_url = self.page.url
        title = await self.page.title()

        # Extract forms and interactive elements using page evaluation
        elements_data = await self.page.evaluate("""
            () => {
                const formsData = [];
                const interactiveSelectors = [];
                
                // Inspect form elements
                document.querySelectorAll('form').forEach((form, formIdx) => {
                    const inputs = form.querySelectorAll('input, select, textarea, button');
                    inputs.forEach((el, elIdx) => {
                        const selector = el.id ? `#${el.id}` : 
                                        (el.name ? `[name="${el.name}"]` : 
                                        `${el.tagName.toLowerCase()}:nth-of-type(${elIdx + 1})`);
                        
                        formsData.push({
                            selector: selector,
                            element_type: el.type || el.tagName.toLowerCase(),
                            name: el.name || null,
                            placeholder: el.placeholder || null,
                            is_required: el.required || false,
                            ref_id: formIdx * 100 + elIdx + 1
                        });
                    });
                });

                // Inspect interactive links & buttons outside forms
                document.querySelectorAll('a[href], button:not(form button)').forEach((el, idx) => {
                    const href = el.getAttribute('href');
                    const text = el.innerText.trim();
                    const selector = el.id ? `#${el.id}` : (href ? `a[href="${href}"]` : `button:nth-of-type(${idx + 1})`);
                    interactiveSelectors.push({
                        selector: selector,
                        href: href || null,
                        text: text || null
                    });
                });

                return { formsData, interactiveSelectors };
            }
        """)

        forms = [FormElement(**item) for item in elements_data.get("formsData", [])]
        interactive = [item["selector"] for item in elements_data.get("interactiveSelectors", []) if item.get("selector")]
        
        # Extract discovered links for further crawling
        discovered_links = []
        for item in elements_data.get("interactiveSelectors", []):
            href = item.get("href")
            if href and self.domain_lock.is_allowed(href):
                # Normalize relative links
                if href.startswith("/"):
                    from urllib.parse import urljoin
                    href = urljoin(current_url, href)
                discovered_links.append(href)

        # Accessibility Tree (AXTree) Snapshot
        axtree_snapshot = None
        try:
            axtree_snapshot = await self.page.accessibility.snapshot()
        except Exception as e:
            logger.warning(f"Failed to capture AXTree snapshot for {current_url}: {e}")

        return RouteNode(
            url=current_url,
            title=title,
            depth=depth,
            forms=forms,
            interactive_selectors=interactive,
            discovered_links=list(set(discovered_links)),
            axtree_snapshot=axtree_snapshot
        )
