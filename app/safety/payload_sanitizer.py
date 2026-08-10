import random
import string

class PayloadSanitizer:
    """
    Generates synthetic, safe test data for form inputs and boundary testing,
    preventing PII contamination or invalid email delivery.
    """
    @staticmethod
    def get_safe_email() -> str:
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"testuser_{rand_str}@example.com"

    @staticmethod
    def get_safe_phone() -> str:
        return "+15550199999"

    @staticmethod
    def get_safe_text(length: int = 10) -> str:
        return "ChaosPilot_" + ''.join(random.choices(string.ascii_letters, k=max(1, length - 11)))

    @staticmethod
    def get_boundary_string(boundary_type: str) -> str:
        if boundary_type == "OVERFLOW_STRING":
            return "A" * 5000
        elif boundary_type == "SPECIAL_CHARS":
            return "<script>alert('chaospilot_xss')</script>\"'--#;&!*"
        elif boundary_type == "SQL_INJECTION_MOCK":
            return "' OR '1'='1"
        elif boundary_type == "UNICODE_EMOJI":
            return "🔥🤖👾💥🚀" * 50
        elif boundary_type == "EMPTY_SPACE":
            return "   "
        return "ChaosPilot_Boundary_Test"
