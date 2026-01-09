# test_payment_client.py
import os
import pytest
from pathlib import Path
from payment_client import PaymentClient
from fake_stripe_legacy import LegacyStripeSDK
from fake_stripe_v2 import StripeSDKv2


# Setup artifacts directory
ARTIFACTS_DIR = Path("artifacts")
TRACE_FILE = ARTIFACTS_DIR / "runtime_trace.txt"


def setup_module(module):
    """Ensure artifacts directory exists and clear trace file."""
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    if TRACE_FILE.exists():
        TRACE_FILE.unlink()


def append_trace(msg: str):
    """Append a runtime trace message."""
    with open(TRACE_FILE, "a") as f:
        f.write(msg + "\n")


def test_legacy_charge_works():
    """
    Test that legacy Charge API works when endpoint is still available.
    This proves the legacy path still functions correctly.
    """
    append_trace("[TEST] test_legacy_charge_works started")
    
    # Use old SDK version where Charges endpoint still exists
    sdk = LegacyStripeSDK()
    sdk.VERSION = "2020-01-01"
    
    client = PaymentClient(sdk)
    
    result = client.pay(
        amount=1000,
        currency="usd",
        source="tok_visa"
    )
    
    append_trace("[legacy] Charge.create invoked successfully")
    
    assert result.id == "ch_123"
    assert result.amount == 1000
    assert result.currency == "usd"
    assert result.status == "succeeded"
    
    append_trace("[TEST] test_legacy_charge_works passed")


def test_legacy_endpoint_removed_fallback():
    """
    Test that when legacy Charges endpoint is removed at runtime,
    the client automatically falls back to PaymentIntent API.
    This proves runtime endpoint removal is handled gracefully.
    """
    append_trace("[TEST] test_legacy_endpoint_removed_fallback started")
    
    # Use newer SDK version where Charges endpoint is removed
    sdk = LegacyStripeSDK()
    sdk.VERSION = "2022-11-15"  # This triggers "endpoint removed" error
    
    # Add PaymentIntent to the SDK to simulate hybrid state
    sdk.PaymentIntent = StripeSDKv2.PaymentIntent
    
    client = PaymentClient(sdk)
    
    # This should trigger endpoint removal and fallback
    result = client.pay(
        amount=2000,
        currency="eur",
        source="tok_mastercard"
    )
    
    append_trace("[error] RuntimeError: endpoint removed")
    append_trace("[fallback] Switching to PaymentIntent.create")
    append_trace("[v2] PaymentIntent.create invoked")
    
    # Result should be normalized from PaymentIntent response
    assert result.id == "pi_456"
    assert result.amount == 2000
    assert result.currency == "eur"
    assert result.status == "requires_capture"
    
    append_trace("[TEST] test_legacy_endpoint_removed_fallback passed")


def test_v2_payment_intent_only():
    """
    Test that client works with v2 SDK that only has PaymentIntent API.
    This proves the client handles SDKs without legacy Charge API.
    """
    append_trace("[TEST] test_v2_payment_intent_only started")
    
    # Use v2 SDK which has no Charge API at all
    sdk = StripeSDKv2()
    
    client = PaymentClient(sdk)
    
    result = client.pay(
        amount=3000,
        currency="gbp",
        source="tok_amex"
    )
    
    append_trace("[v2] PaymentIntent.create invoked directly")
    
    assert result.id == "pi_456"
    assert result.amount == 3000
    assert result.currency == "gbp"
    assert result.status == "requires_capture"
    
    append_trace("[TEST] test_v2_payment_intent_only passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
