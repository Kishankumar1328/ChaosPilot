import os
import logging
from typing import List
from app.models.testplan import TestStep

logger = logging.getLogger(__name__)

REPRODUCTION_SCRIPT_TEMPLATE = """# Standalone Playwright Reproduction Script for Bug: {bug_title}
# Generated automatically by ChaosPilot Autonomous AI QA Engineer

import asyncio
from playwright.async_api import async_playwright

async def reproduce():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={{"width": 1280, "height": 720}})
        page = await context.new_page()

        # Listen for console errors & network failures
        page.on("console", lambda msg: print(f"[CONSOLE {{msg.type.upper()}}] {{msg.text}}"))
        page.on("response", lambda res: print(f"[NETWORK {{res.status}}] {{res.url}}") if res.status >= 400 else None)

        print("--> Navigating to initial route: {target_route}")
        await page.goto("{target_route}", wait_until="networkidle")

{step_code}

        print("--> Reproduction sequence completed. Holding open for inspection (5s)...")
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(reproduce())
"""

class ReproductionScriptGenerator:
    """
    Generates runnable standalone Python Playwright scripts that recreate
    the exact bug reproduction sequence.
    """
    @staticmethod
    def generate_script(
        run_id: str,
        bug_id: str,
        bug_title: str,
        target_route: str,
        steps: List[TestStep],
        output_dir: str = "./artifacts"
    ) -> str:
        bug_dir = os.path.join(output_dir, run_id, bug_id)
        os.makedirs(bug_dir, exist_ok=True)
        script_path = os.path.join(bug_dir, "reproduce_bug.py")

        formatted_steps = []
        for step in steps:
            selector = step.target_selector or ""
            value = step.value or ""
            action = step.action.value

            if action == "NAVIGATE":
                formatted_steps.append(f'        await page.goto("{value or target_route}", wait_until="networkidle")')
            elif action == "CLICK":
                formatted_steps.append(f'        await page.click("{selector}")')
            elif action == "FILL":
                formatted_steps.append(f'        await page.fill("{selector}", "{value}")')
            elif action == "SELECT":
                formatted_steps.append(f'        await page.select_option("{selector}", "{value}")')
            elif action == "CHECK":
                formatted_steps.append(f'        await page.check("{selector}")')
            elif action == "PRESS":
                formatted_steps.append(f'        await page.press("{selector}", "{value or "Enter"}")')

        step_code = "\n".join(formatted_steps) if formatted_steps else "        pass"

        content = REPRODUCTION_SCRIPT_TEMPLATE.format(
            bug_title=bug_title,
            target_route=target_route,
            step_code=step_code
        )

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Generated bug reproduction script at: {script_path}")
        return script_path
