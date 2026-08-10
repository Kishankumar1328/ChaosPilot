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
            response = await self.page.goto(url, wait_until="networkidle", timeout=15000)
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
                document.querySelectorAll('a[href], button, input[type="button"], input[type="submit"]').forEach((el) => {
                    if (el.href) {
                        interactiveSelectors.push(el.href);
                    } else if (el.id) {
                        interactiveSelectors.push(`#${el.id}`);
                    }
                });

                return { formsData, interactiveSelectors };
            }
        """)

        forms = [FormElement(**f) for f in elements_data.get("formsData", [])]
        interactive = elements_data.get("interactiveSelectors", [])

        # Extract lightweight accessibility tree snapshot
        axtree_snippet = ""
        try:
            snapshot = await self.page.accessibility.snapshot()
            if snapshot:
                axtree_snippet = str(snapshot)[:2000]  # Limit size for LLM context optimization
        except Exception as e:
            logger.warning(f"Failed to capture accessibility snapshot: {e}")

        return RouteNode(
            url=current_url,
            title=title,
            depth=depth,
            forms=forms,
            interactive_selectors=interactive,
            axtree_snippet=axtree_snippet
        )
