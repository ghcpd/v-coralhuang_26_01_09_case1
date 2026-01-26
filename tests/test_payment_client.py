import os
from pathlib import Path

import pytest

from payment_client import PaymentClient, NormalizedPayment
import fake_stripe_legacy
import fake_stripe_v2

ARTIFACT = Path("artifacts/runtime_trace.txt")


def read_trace():
    if not ARTIFACT.exists():
        return ""
    return ARTIFACT.read_text()


def clear_trace():
    if ARTIFACT.exists():
        ARTIFACT.unlink()


def test_legacy_charge_works():
    """Legacy Charges API still works"""
    clear_trace()

    sdk = fake_stripe_legacy.LegacyStripeSDK
    client = PaymentClient(sdk=sdk)

    p = client.pay(amount=100, currency="usd", source="tok_visa")

    assert isinstance(p, NormalizedPayment)
    assert p.id == "ch_123"
    assert p.amount == 100
    assert p.currency == "usd"
    assert p.status == "succeeded"

    trace = read_trace()
    assert "Charge.create invoked" in trace


def test_legacy_endpoint_removed_fallback():
    """When legacy endpoint is removed at runtime, fallback to PaymentIntent"""
    clear_trace()

    # Simulate SDK that has both Charge (which will raise endpoint removed)
    # and PaymentIntent available for fallback
    sdk = fake_stripe_legacy.LegacyStripeSDK
    sdk.VERSION = "2022-11-15"

    # attach v2 PaymentIntent to same SDK to emulate upgraded SDK with both classes
    sdk.PaymentIntent = fake_stripe_v2.PaymentIntent

    client = PaymentClient(sdk=sdk)

    p = client.pay(amount=200, currency="eur", source="tok_amex")

    assert isinstance(p, NormalizedPayment)
    # for v2 flow the normalized id should be the latest_charge from PaymentIntent response
    assert p.id == "ch_456"
    assert p.amount == 200
    assert p.currency == "eur"
    # v2 returned status 'requires_capture' so we expose that
    assert p.status == "requires_capture"

    trace = read_trace()
    assert "Charge.create invoked" in trace
    assert "[error] endpoint removed" in trace
    assert "Switching to PaymentIntent.create" in trace
    assert "PaymentIntent.create invoked" in trace


def test_v2_payment_intent_only():
    """SDKs that only provide PaymentIntent should work"""
    clear_trace()

    sdk = fake_stripe_v2.StripeSDKv2
    client = PaymentClient(sdk=sdk)

    p = client.pay(amount=300, currency="gbp", source="tok_mastercard")

    assert isinstance(p, NormalizedPayment)
    assert p.id == "ch_456"
    assert p.amount == 300
    assert p.currency == "gbp"
    assert p.status == "requires_capture"

    trace = read_trace()
    assert "PaymentIntent.create invoked" in trace
    # Should not have tried legacy Charge.create
    assert "Charge.create invoked" not in trace
