import logging
from app.models.state import ChaosPilotState, RunStatus
from app.safety.domain_lock import DomainLock
from app.tools.browser_manager import BrowserManager
from app.tools.navigator import Navigator

logger = logging.getLogger(__name__)

async def discovery_node(state: ChaosPilotState) -> ChaosPilotState:
    """
    Discovery Node (Explorer Agent):
    Crawls the target URL up to max_depth and max_pages to build the canonical SiteMap.
    """
    state.status = RunStatus.DISCOVERING
    state.logs.append(f"🔍 [ExplorerAgent] Starting autonomous application discovery for target: {state.target_url}")
    logger.info(f"ExplorerAgent running for {state.target_url}")

    domain_lock = DomainLock(state.target_url)
    browser_mgr = BrowserManager()
    await browser_mgr.start(headless=True)

    try:
        navigator = Navigator(browser_mgr.page, domain_lock)
        success, msg, status_code = await navigator.navigate_to(state.target_url)
        
        if not success:
            state.logs.append(f"❌ [ExplorerAgent] Failed to open target URL: {msg}")
            state.status = RunStatus.FAILED
            state.error_summary = msg
            await browser_mgr.close()
            return state

        # Discover primary route node
        route_node = await navigator.extract_route_node(depth=0)
        state.site_map[state.target_url] = route_node
        state.visited_urls.append(state.target_url)
        state.logs.append(f"✅ [ExplorerAgent] Discovered root route '{route_node.title}' with {len(route_node.forms)} forms and {len(route_node.interactive_selectors)} interactive links")

        # Discover child links within domain lock up to max_pages
        unvisited = [url for url in route_node.interactive_selectors if domain_lock.is_allowed(url)]
        
        depth = 1
        while unvisited and len(state.visited_urls) < state.max_pages and depth <= state.max_depth:
            next_url = unvisited.pop(0)
            if next_url in state.visited_urls:
                continue

            state.logs.append(f"🔍 [ExplorerAgent] Crawling secondary route: {next_url}")
            nav_ok, nav_msg, _ = await navigator.navigate_to(next_url)
            
            if nav_ok:
                child_node = await navigator.extract_route_node(depth=depth)
                state.site_map[next_url] = child_node
                state.visited_urls.append(next_url)
                state.logs.append(f"✅ [ExplorerAgent] Mapped route '{child_node.title}' ({len(child_node.forms)} forms)")
                
                # Add child links
                for child_link in child_node.interactive_selectors:
                    if domain_lock.is_allowed(child_link) and child_link not in state.visited_urls and child_link not in unvisited:
                        unvisited.append(child_link)

        state.logs.append(f"🎉 [ExplorerAgent] Discovery complete. Total routes mapped: {len(state.site_map)}")

    except Exception as e:
        logger.error(f"ExplorerAgent error: {e}")
        state.logs.append(f"❌ [ExplorerAgent] Unexpected discovery error: {str(e)}")
        state.status = RunStatus.FAILED
        state.error_summary = str(e)
    finally:
        await browser_mgr.close()

    return state
