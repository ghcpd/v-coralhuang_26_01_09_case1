# fake_stripe_v2.py
from __future__ import annotations
from typing import Any, Dict


class PaymentIntent:
    @staticmethod
    def create(**kwargs: Any) -> Dict[str, Any]:
        # v2 contract drift:
        # - 'payment_method' instead of 'source'
        # - requires capture_method
        if "payment_method" not in kwargs:
            raise TypeError("PaymentIntent.create requires 'payment_method'")
        if kwargs.get("capture_method") not in ("automatic", "manual"):
            raise TypeError("PaymentIntent.create requires valid 'capture_method'")

        return {
            "object": "payment_intent",
            "id": "pi_456",
            "amount": int(kwargs["amount"]),
            "currency": str(kwargs["currency"]),
            "status": "requires_capture",
            "latest_charge": "ch_456",
            "_request": dict(kwargs),
        }


class StripeSDKv2:
    PaymentIntent = PaymentIntent
