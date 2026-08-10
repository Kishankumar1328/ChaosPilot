from app.safety.domain_lock import DomainLock
from app.safety.action_interceptor import ActionInterceptor
from app.safety.payload_sanitizer import PayloadSanitizer

def test_domain_lock():
    lock = DomainLock("https://target.example.com/app")
    assert lock.is_allowed("https://target.example.com/dashboard") is True
    assert lock.is_allowed("https://sub.target.example.com/api") is True
    assert lock.is_allowed("https://malicious.com") is False
    assert lock.is_allowed("https://stripe.com/checkout") is False

def test_action_interceptor():
    interceptor = ActionInterceptor(allow_destructive=False)
    
    # Allowed actions
    ok, _ = interceptor.check_action("CLICK", "button#submit", "Send Message")
    assert ok is True
    
    # Blocked destructive actions
    ok, reason = interceptor.check_action("CLICK", "button#delete-account", "Delete Account")
    assert ok is False
    assert "GUARDRAIL_BLOCKED" in reason

def test_payload_sanitizer():
    email = PayloadSanitizer.get_safe_email()
    assert "@example.com" in email
    
    overflow = PayloadSanitizer.get_boundary_string("OVERFLOW_STRING")
    assert len(overflow) == 5000
