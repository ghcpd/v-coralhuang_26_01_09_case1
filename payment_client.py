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
        import os
        from pathlib import Path

        os.makedirs("artifacts", exist_ok=True)
        trace_file = Path("artifacts/runtime_trace.txt")

        def _trace(line: str) -> None:
            with trace_file.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

        # Try legacy Charges API if available
        if hasattr(self.sdk, "Charge"):
            _trace("[legacy] Charge.create invoked")
            req: Dict[str, Any] = {
                "amount": amount,
                "currency": currency,
                "source": source,  # legacy field
                "_sdk": self.sdk,  # used by fake legacy to simulate endpoint removal by version
            }

            try:
                resp = self.sdk.Charge.create(**req)

                return NormalizedPayment(
                    id=resp["id"],
                    amount=resp["amount"],
                    currency=resp["currency"],
                    status=resp["status"],
                )

            except RuntimeError as e:
                # detected runtime endpoint removal; try fallback
                _trace(f"[error] {e}")
                if hasattr(self.sdk, "PaymentIntent"):
                    _trace("[fallback] Switching to PaymentIntent.create")
                    _trace("[v2] PaymentIntent.create invoked")
                    pi_req = {
                        "amount": amount,
                        "currency": currency,
                        "payment_method": source,
                        "capture_method": "automatic",
                    }
                    resp = self.sdk.PaymentIntent.create(**pi_req)

                    # normalize: use latest_charge when available (v2) else id
                    pid = resp.get("latest_charge") or resp.get("id")

                    return NormalizedPayment(
                        id=pid,
                        amount=resp["amount"],
                        currency=resp["currency"],
                        status=resp["status"],
                    )
                # no fallback available, re-raise
                raise

        # Legacy Charge not present or was not used; try v2 PaymentIntent directly
        if hasattr(self.sdk, "PaymentIntent"):
            _trace("[v2] PaymentIntent.create invoked")
            resp = self.sdk.PaymentIntent.create(
                amount=amount, currency=currency, payment_method=source, capture_method="automatic"
            )
            pid = resp.get("latest_charge") or resp.get("id")
            return NormalizedPayment(id=pid, amount=resp["amount"], currency=resp["currency"], status=resp["status"])

        # No supported methods available
        raise RuntimeError("no supported payment method available")
