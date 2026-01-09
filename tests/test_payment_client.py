import os

from payment_client import PaymentClient, NormalizedPayment
import fake_stripe_legacy as legacy_mod
import fake_stripe_v2 as v2_mod


def _read_trace() -> str:
    with open("artifacts/runtime_trace.txt", "r", encoding="utf-8") as f:
        return f.read()


def test_legacy_charge_works():
    """Legacy Charges API still works when endpoint exists."""
    # ensure clean slate
    legacy_mod.LegacyStripeSDK.VERSION = "2020-01-01"
    sdk = legacy_mod.LegacyStripeSDK()
    client = PaymentClient(sdk)

    out = client.pay(amount=1000, currency="usd", source="src_legacy")

    assert isinstance(out, NormalizedPayment)
    assert out.id == "ch_123"
    assert out.amount == 1000
    assert out.currency == "usd"
    assert out.status == "succeeded"

    trace = _read_trace()
    assert "[legacy] Charge.create invoked" in trace
    assert "[fallback]" not in trace


def test_legacy_endpoint_removed_fallback():
    """When legacy endpoint is removed at runtime, we automatically fallback to v2."""
    legacy_mod.LegacyStripeSDK.VERSION = "2022-11-15"
    sdk = legacy_mod.LegacyStripeSDK()
    client = PaymentClient(sdk)

    out = client.pay(amount=2000, currency="usd", source="src_fallback")

    # Should return normalized result coming from PaymentIntent
    assert isinstance(out, NormalizedPayment)
    assert out.id == "pi_456"
    assert out.amount == 2000
    assert out.currency == "usd"
    assert out.status == "requires_capture"

    trace = _read_trace()
    # verify the legacy path was attempted and then fallback occurred
    assert "[legacy] Charge.create invoked" in trace
    assert "[error] RuntimeError: endpoint removed" in trace
    assert "[fallback] Switching to PaymentIntent.create" in trace
    assert "[v2] PaymentIntent.create invoked" in trace


def test_v2_payment_intent_only():
    """SDKs that only expose PaymentIntent should work without legacy Charge."""
    sdk = v2_mod.StripeSDKv2()
    client = PaymentClient(sdk)

    out = client.pay(amount=3000, currency="eur", source="src_pm")

    assert isinstance(out, NormalizedPayment)
    assert out.id == "pi_456"
    assert out.amount == 3000
    assert out.currency == "eur"
    assert out.status == "requires_capture"

    trace = _read_trace()
    assert "[v2] PaymentIntent.create invoked" in trace
