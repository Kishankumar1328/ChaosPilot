import os
import logging
from typing import Optional
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page
from app.tools.listener import ConsoleNetworkListener

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Manages the lifecycle of Playwright Chromium instances, browser contexts,
    tracing, and network listeners. Supports standard Desktop User-Agent for seamless external crawling.
    """
    def __init__(self, trace_dir: str = "./artifacts/traces"):
        self.trace_dir = trace_dir
        os.makedirs(self.trace_dir, exist_ok=True)
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.listener = ConsoleNetworkListener()

    async def start(self, headless: bool = True):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        # Enable trace recording for failure playback
        await self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.page = await self.context.new_page()
        self.listener.attach_to_page(self.page)
        logger.info("BrowserManager started Chromium browser instance with Desktop User-Agent.")

    async def stop_tracing(self, trace_filename: str) -> str:
        trace_path = os.path.join(self.trace_dir, trace_filename)
        if self.context:
            await self.context.tracing.stop(path=trace_path)
            logger.info(f"Trace recorded to {trace_path}")
        return trace_path

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("BrowserManager closed browser session.")
