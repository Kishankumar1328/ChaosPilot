import logging
from typing import List
from playwright.async_api import Page, Request, Response, ConsoleMessage

logger = logging.getLogger(__name__)

class ConsoleNetworkListener:
    """
    Captures console errors and network failures (HTTP 4xx/5xx) during browser sessions.
    """
    def __init__(self):
        self.console_errors: List[str] = []
        self.network_errors: List[str] = []

    def attach_to_page(self, page: Page):
        self.console_errors.clear()
        self.network_errors.clear()

        def handle_console(msg: ConsoleMessage):
            if msg.type in ["error", "warning"]:
                log_text = f"[{msg.type.upper()}] {msg.text}"
                self.console_errors.append(log_text)
                logger.debug(f"Console Captured: {log_text}")

        def handle_response(response: Response):
            if response.status >= 400:
                err_text = f"HTTP {response.status} {response.request.method} -> {response.url}"
                self.network_errors.append(err_text)
                logger.warning(f"Network Captured: {err_text}")

        def handle_page_error(error: Exception):
            err_text = f"[UNCAUGHT_EXCEPTION] {str(error)}"
            self.console_errors.append(err_text)
            logger.error(err_text)

        page.on("console", handle_console)
        page.on("response", handle_response)
        page.on("pageerror", handle_page_error)

    def get_and_clear_logs(self):
        c_errs = list(self.console_errors)
        n_errs = list(self.network_errors)
        return c_errs, n_errs
