import logging
from app.models.state import ChaosPilotState, RunStatus
from app.safety.domain_lock import DomainLock
from app.tools.browser_manager import BrowserManager
from app.tools.navigator import Navigator
from app.tools.preflight import TargetPreflight

logger = logging.getLogger(__name__)

async def discovery_node(state: ChaosPilotState) -> ChaosPilotState:
    """
    Discovery Node (Explorer Agent):
    Executes a preflight health check first, then crawls target_url up to max_depth/max_pages.
    If preflight check indicates target is unreachable or DNS failed, sets TARGET_UNAVAILABLE and exits cleanly.
    """
    state.status = RunStatus.DISCOVERING
    state.logs.append(f"🔍 [ExplorerAgent] Starting target preflight check for: {state.target_url}")
    logger.info(f"ExplorerAgent running for {state.target_url}")

    # 1. Target Preflight Health Check
    health = await TargetPreflight.check_health(state.target_url, timeout_seconds=8.0)
    state.target_reachable = health.reachable
    
    if not health.reachable:
        state.logs.append(f"⛔ [ExplorerAgent] TARGET UNAVAILABLE ({health.error_kind}). Preflight check failed for {state.target_url}.")
        state.status = RunStatus.TARGET_UNAVAILABLE
        state.error_summary = f"Target application unreachable: {health.error_kind}"
        return state

    state.logs.append(f"✅ [ExplorerAgent] Target preflight health OK (HTTP {health.status_code}, DOM Available: {health.dom_available}). Commencing discovery crawl...")

    domain_lock = DomainLock(state.target_url)
    browser_mgr = BrowserManager()
    await browser_mgr.start(headless=True)

    try:
        navigator = Navigator(browser_mgr.page, domain_lock)
        success, msg, status_code = await navigator.navigate_to(state.target_url)
        
        if not success:
            state.logs.append(f"⚠️ [ExplorerAgent] Initial navigation warning: {msg}")

        # Discover primary route node
        route_node = await navigator.extract_route_node(depth=0)
        state.site_map[state.target_url] = route_node
        state.visited_urls.append(state.target_url)
        state.logs.append(f"✅ [ExplorerAgent] Discovered root route '{route_node.title or state.target_url}' with {len(route_node.forms)} forms and {len(route_node.interactive_selectors)} interactive links")

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
                state.logs.append(f"✅ [ExplorerAgent] Mapped route '{child_node.title or next_url}' ({len(child_node.forms)} forms)")
                
                # Add child links
                for child_link in child_node.interactive_selectors:
                    if domain_lock.is_allowed(child_link) and child_link not in state.visited_urls and child_link not in unvisited:
                        unvisited.append(child_link)
            else:
                state.logs.append(f"ℹ️ [ExplorerAgent] Skipped unnavigable secondary link: {next_url}")

            depth += 1

        state.logs.append(f"✅ [ExplorerAgent] SiteMap discovery complete. {len(state.site_map)} routes mapped.")

    except Exception as e:
        logger.error(f"ExplorerAgent error: {e}")
        state.logs.append(f"❌ [ExplorerAgent] Discovery error: {str(e)}")
        state.status = RunStatus.FAILED
        state.error_summary = str(e)
    finally:
        await browser_mgr.close()

    return state
