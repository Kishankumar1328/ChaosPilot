import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Pattern matching dangerous/destructive keywords
DESTRUCTIVE_KEYWORDS_PATTERN = re.compile(
    r"(?i)\b(delete|drop|purge|wipe|destroy|reset-db|cancel-subscription|clear-all|remove-account|format|truncate)\b"
)

class ActionInterceptor:
    """
    Prevents autonomous agents from clicking dangerous buttons or submitting 
    forms that perform destructive account or database actions.
    """
    def __init__(self, allow_destructive: bool = False):
        self.allow_destructive = allow_destructive

    def check_action(self, action_type: str, selector_or_text: str, value: str = "") -> Tuple[bool, str]:
        if self.allow_destructive:
            return True, "Destructive actions allowed by explicit configuration"

        combined_target = f"{selector_or_text} {value}"
        match = DESTRUCTIVE_KEYWORDS_PATTERN.search(combined_target)
        
        if match:
            keyword = match.group(0)
            reason = f"GUARDRAIL_BLOCKED: Action Interceptor blocked dangerous action matching keyword '{keyword}' in target '{selector_or_text}'"
            logger.warning(reason)
            return False, reason

        return True, "Action permitted"
