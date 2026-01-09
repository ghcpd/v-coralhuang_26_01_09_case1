# payment_client.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class NormalizedPayment:
    id: str
    amount: int
    currency: str
    status: str


class PaymentClient:
    """
    Baseline intentionally supports ONLY legacy Charges API.

    Agent should write tests and migrate this client to support both:
      - legacy: sdk.Charge.create(amount, currency, source)
      - v2:     sdk.PaymentIntent.create(amount, currency, payment_method, capture_method="automatic")

    Additionally, legacy may fail at runtime with:
      RuntimeError("endpoint removed")
    simulating an outdated endpoint removed after an SDK/backend upgrade.
    """
    def __init__(self, sdk: Any):
        self.sdk = sdk

    def pay(self, *, amount: int, currency: str, source: str) -> NormalizedPayment:
        req: Dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "source": source,  # legacy field
            "_sdk": self.sdk,  # used by fake legacy to simulate endpoint removal by version
        }

        # This will fail for:
        # - v2 SDK which has no Charge API
        # - legacy SDK when endpoint removed for certain versions
        resp = self.sdk.Charge.create(**req)

        return NormalizedPayment(
            id=resp["id"],
            amount=resp["amount"],
            currency=resp["currency"],
            status=resp["status"],
        )
