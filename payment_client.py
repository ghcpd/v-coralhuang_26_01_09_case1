# payment_client.py
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Any, Dict


ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
RUNTIME_TRACE = os.path.join(ARTIFACTS_DIR, "runtime_trace.txt")


def _append_trace(line: str) -> None:
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    with open(RUNTIME_TRACE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


@dataclass(frozen=True)
class NormalizedPayment:
    id: str
    amount: int
    currency: str
    status: str


class PaymentClient:
    """
    Client supporting both legacy Charges and v2 PaymentIntent with automatic fallback.

    Selection is done at runtime via attribute detection and exception handling only.
    """
    def __init__(self, sdk: Any):
        self.sdk = sdk

    def _call_charge(self, amount: int, currency: str, source: str) -> Dict[str, Any]:
        # prepare legacy request
        req: Dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "source": source,
            "_sdk": self.sdk,
        }
        _append_trace("[legacy] Charge.create invoked")
        return self.sdk.Charge.create(**req)

    def _call_payment_intent(self, amount: int, currency: str, source: str) -> Dict[str, Any]:
        # map legacy "source" -> v2 "payment_method" and apply capture_method
        req: Dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "payment_method": source,
            "capture_method": "automatic",
        }
        _append_trace("[v2] PaymentIntent.create invoked")
        return self.sdk.PaymentIntent.create(**req)

    def pay(self, *, amount: int, currency: str, source: str) -> NormalizedPayment:
        # Try legacy Charges API if present
        if hasattr(self.sdk, "Charge"):
            try:
                resp = self._call_charge(amount, currency, source)
            except RuntimeError as exc:
                # endpoint removed at runtime: fallback to PaymentIntent
                _append_trace(f"[error] RuntimeError: {exc}")
                if not hasattr(self.sdk, "PaymentIntent"):
                    raise
                _append_trace("[fallback] Switching to PaymentIntent.create")
                resp = self._call_payment_intent(amount, currency, source)
        else:
            # No legacy API available; use PaymentIntent directly
            resp = self._call_payment_intent(amount, currency, source)

        # Normalize response from either API surface
        return NormalizedPayment(
            id=resp["id"],
            amount=int(resp["amount"]),
            currency=str(resp["currency"]),
            status=str(resp["status"]),
        )
