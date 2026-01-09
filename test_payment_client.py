# test_payment_client.py
from __future__ import annotations
import os
from fake_stripe_legacy import LegacyStripeSDK, Charge
from fake_stripe_v2 import StripeSDKv2, PaymentIntent
from payment_client import PaymentClient, NormalizedPayment

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
RUNTIME_TRACE = os.path.join(ARTIFACTS_DIR, "runtime_trace.txt")


def _read_trace() -> str:
    with open(RUNTIME_TRACE, "r", encoding="utf-8") as fh:
        return fh.read()


def _reset_artifacts():
    if os.path.exists(ARTIFACTS_DIR):
        for fn in os.listdir(ARTIFACTS_DIR):
            os.remove(os.path.join(ARTIFACTS_DIR, fn))
    else:
        os.makedirs(ARTIFACTS_DIR)


# Reset artifacts once for the whole test module so the single runtime_trace.txt
# contains evidence from all test runs (legacy, endpoint removal/fallback, v2).
_reset_artifacts()


def test_legacy_charge_works():
    """Legacy Charges API works when endpoint exists"""

    sdk = LegacyStripeSDK
    sdk.VERSION = "2020-01-01"

    client = PaymentClient(sdk=sdk)
    out = client.pay(amount=1500, currency="usd", source="tok_visa")

    assert isinstance(out, NormalizedPayment)
    assert out.id == "ch_123"
    assert out.amount == 1500
    assert out.currency == "usd"
    assert out.status == "succeeded"

    trace = _read_trace()
    assert "Charge.create invoked" in trace


def test_legacy_endpoint_removed_fallback():
    """When legacy endpoint raises RuntimeError, fallback to PaymentIntent"""

    class HybridSDK:
        # runtime upgraded version that causes legacy endpoint removal
        VERSION = "2022-11-15"
        Charge = Charge
        PaymentIntent = PaymentIntent

    client = PaymentClient(sdk=HybridSDK)
    out = client.pay(amount=2000, currency="eur", source="tok_mastercard")

    assert isinstance(out, NormalizedPayment)
    assert out.id == "pi_456"
    assert out.amount == 2000
    assert out.currency == "eur"
    # PaymentIntent returns "requires_capture" in the fake v2
    assert out.status == "requires_capture"

    trace = _read_trace()
    assert "Charge.create invoked" in trace
    assert "RuntimeError: endpoint removed" in trace
    assert "Switching to PaymentIntent.create" in trace
    assert "PaymentIntent.create invoked" in trace


def test_v2_payment_intent_only():
    """When SDK only has PaymentIntent, use it directly"""

    sdk = StripeSDKv2
    client = PaymentClient(sdk=sdk)

    out = client.pay(amount=500, currency="gbp", source="tok_amex")

    assert isinstance(out, NormalizedPayment)
    assert out.id == "pi_456"
    assert out.amount == 500
    assert out.currency == "gbp"
    assert out.status == "requires_capture"

    trace = _read_trace()
    assert "PaymentIntent.create invoked" in trace
