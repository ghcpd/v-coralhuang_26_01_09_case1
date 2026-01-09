import os
import pytest
from payment_client import PaymentClient, NormalizedPayment
from fake_stripe_legacy import LegacyStripeSDK
from fake_stripe_v2 import StripeSDKv2, PaymentIntent


def test_legacy_charge_works():
    sdk = LegacyStripeSDK()
    sdk.VERSION = "2020-01-01"
    client = PaymentClient(sdk)
    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/runtime_trace.txt", "w") as f:
        f.write("")
    result = client.pay(amount=100, currency="usd", source="tok_123")
    assert result.id == "ch_123"
    assert result.amount == 100
    assert result.currency == "usd"
    assert result.status == "succeeded"
    with open("artifacts/runtime_trace.txt") as f:
        trace = f.read()
    assert "[legacy] Charge.create invoked" in trace
    assert "[success] Charge succeeded" in trace


def test_legacy_endpoint_removed_fallback():
    sdk = LegacyStripeSDK()
    sdk.VERSION = "2022-11-15"
    sdk.PaymentIntent = PaymentIntent  # Simulate SDK upgrade with PaymentIntent available
    client = PaymentClient(sdk)
    with open("artifacts/runtime_trace.txt", "w") as f:
        f.write("")
    result = client.pay(amount=100, currency="usd", source="tok_123")
    assert result.id == "pi_456"
    assert result.amount == 100
    assert result.currency == "usd"
    assert result.status == "requires_capture"
    with open("artifacts/runtime_trace.txt") as f:
        trace = f.read()
    assert "[legacy] Charge.create invoked" in trace
    assert "[error] RuntimeError: endpoint removed" in trace
    assert "[fallback] Switching to PaymentIntent.create" in trace


def test_v2_payment_intent_only():
    sdk = StripeSDKv2()
    client = PaymentClient(sdk)
    with open("artifacts/runtime_trace.txt", "w") as f:
        f.write("")
    result = client.pay(amount=100, currency="usd", source="tok_123")
    assert result.id == "pi_456"
    assert result.amount == 100
    assert result.currency == "usd"
    assert result.status == "requires_capture"
    with open("artifacts/runtime_trace.txt") as f:
        trace = f.read()
    assert "[v2] PaymentIntent.create invoked" in trace