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
    Payment client that supports both legacy Charges API and modern PaymentIntent API.

    Handles three scenarios:
      1. Legacy SDK with Charges API still available
      2. Legacy SDK with Charges endpoint removed (automatic fallback to PaymentIntent)
      3. Modern SDK with only PaymentIntent API

    The client automatically detects capabilities and falls back gracefully.
    """
    def __init__(self, sdk: Any):
        self.sdk = sdk

    def pay(self, *, amount: int, currency: str, source: str) -> NormalizedPayment:
        # Try legacy Charge API first if it exists
        if hasattr(self.sdk, 'Charge'):
            try:
                req: Dict[str, Any] = {
                    "amount": amount,
                    "currency": currency,
                    "source": source,
                    "_sdk": self.sdk,
                }
                resp = self.sdk.Charge.create(**req)
                return self._normalize_charge_response(resp)
            except RuntimeError as e:
                if "endpoint removed" in str(e):
                    # Endpoint removed at runtime, fallback to PaymentIntent
                    return self._pay_with_payment_intent(amount, currency, source)
                raise
        
        # No Charge API available, use PaymentIntent directly
        return self._pay_with_payment_intent(amount, currency, source)

    def _pay_with_payment_intent(self, amount: int, currency: str, source: str) -> NormalizedPayment:
        """Use PaymentIntent API with proper request mapping."""
        req: Dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "payment_method": source,  # Map source -> payment_method
            "capture_method": "automatic",
        }
        resp = self.sdk.PaymentIntent.create(**req)
        return self._normalize_payment_intent_response(resp)

    def _normalize_charge_response(self, resp: Dict[str, Any]) -> NormalizedPayment:
        """Normalize legacy Charge response."""
        return NormalizedPayment(
            id=resp["id"],
            amount=resp["amount"],
            currency=resp["currency"],
            status=resp["status"],
        )

    def _normalize_payment_intent_response(self, resp: Dict[str, Any]) -> NormalizedPayment:
        """Normalize PaymentIntent response to match expected schema."""
        return NormalizedPayment(
            id=resp["id"],
            amount=resp["amount"],
            currency=resp["currency"],
            status=resp["status"],
        )
