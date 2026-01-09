# fake_stripe_legacy.py
from __future__ import annotations
from typing import Any, Dict


class Charge:
    @staticmethod
    def create(**kwargs: Any) -> Dict[str, Any]:
        # One-line "endpoint removed" simulation:
        # If SDK version is >= 2022-11-15, pretend Charges endpoint is removed.
        if getattr(kwargs.get("_sdk"), "VERSION", "0") >= "2022-11-15":
            raise RuntimeError("endpoint removed")

        # legacy contract: amount, currency, source
        if "source" not in kwargs:
            raise TypeError("legacy Charge.create requires 'source'")

        return {
            "object": "charge",
            "id": "ch_123",
            "amount": int(kwargs["amount"]),
            "currency": str(kwargs["currency"]),
            "status": "succeeded",
            "_request": dict(kwargs),
        }


class LegacyStripeSDK:
    """
    Simulate legacy SDK that still has Charges API, but the backend endpoint may be removed
    after a certain version cutoff.
    """
    VERSION = "2020-01-01"  # agent/tests can override this to simulate upgrade breakage

    Charge = Charge
