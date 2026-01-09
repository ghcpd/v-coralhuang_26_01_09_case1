# payment_client.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
import os


@dataclass(frozen=True)
class NormalizedPayment:
    id: str
    amount: int
    currency: str
    status: str


class PaymentClient:
    """
    Migrated to support both legacy and v2 APIs with fallback.

    - Tries legacy Charge.create first.
    - If Charge not available (AttributeError), uses PaymentIntent.
    - If Charge raises RuntimeError("endpoint removed"), falls back to PaymentIntent.
    """
    def __init__(self, sdk: Any):
        self.sdk = sdk

    def pay(self, *, amount: int, currency: str, source: str) -> NormalizedPayment:
        os.makedirs("artifacts", exist_ok=True)
        with open("artifacts/runtime_trace.txt", "a") as f:
            f.write("[legacy] Charge.create invoked\n")

        req_charge: Dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "source": source,
            "_sdk": self.sdk,
        }

        try:
            resp = self.sdk.Charge.create(**req_charge)
            with open("artifacts/runtime_trace.txt", "a") as f:
                f.write("[success] Charge succeeded\n")
        except AttributeError:
            # No Charge API, use PaymentIntent
            with open("artifacts/runtime_trace.txt", "a") as f:
                f.write("[v2] PaymentIntent.create invoked\n")
            req_pi = {
                "amount": amount,
                "currency": currency,
                "payment_method": source,
                "capture_method": "automatic",
            }
            resp = self.sdk.PaymentIntent.create(**req_pi)
        except RuntimeError as e:
            if "endpoint removed" in str(e):
                with open("artifacts/runtime_trace.txt", "a") as f:
                    f.write(f"[error] {type(e).__name__}: {e}\n")
                    f.write("[fallback] Switching to PaymentIntent.create\n")
                req_pi = {
                    "amount": amount,
                    "currency": currency,
                    "payment_method": source,
                    "capture_method": "automatic",
                }
                resp = self.sdk.PaymentIntent.create(**req_pi)
            else:
                raise

        return NormalizedPayment(
            id=resp["id"],
            amount=resp["amount"],
            currency=resp["currency"],
            status=resp["status"],
        )
