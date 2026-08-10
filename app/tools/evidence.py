import os
import logging
from typing import Dict
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class EvidenceRecorder:
    """
    Captures visual PNG screenshots and stores evidence artifacts for bug reports.
    """
    def __init__(self, output_dir: str = "./artifacts"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    async def capture_screenshot(self, page: Page, run_id: str, bug_id: str) -> str:
        bug_dir = os.path.join(self.output_dir, run_id, bug_id)
        os.makedirs(bug_dir, exist_ok=True)
        screenshot_path = os.path.join(bug_dir, "screenshot.png")
        
        try:
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Captured full page screenshot: {screenshot_path}")
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            
        return screenshot_path
