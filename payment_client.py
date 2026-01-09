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
        # Ensure artifacts dir exists
        from pathlib import Path
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        trace_file = artifacts_dir / "runtime_trace.txt"

        def _append_trace(line: str) -> None:
            with trace_file.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

        req: Dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "source": source,  # legacy field
            "_sdk": self.sdk,  # used by fake legacy to simulate endpoint removal by version
        }

        # Try legacy Charge API first
        try:
            _append_trace("[legacy] Charge.create invoked")
            resp = self.sdk.Charge.create(**req)  # type: ignore[attr-defined]
        except AttributeError:
            # SDK does not have Charge API; try v2 directly
            _append_trace("[error] legacy Charge API not present")
            resp = self._create_payment_intent(amount, currency, source, _append_trace)
        except RuntimeError as e:
            # Legacy endpoint removed at runtime: fallback
            _append_trace(f"[error] RuntimeError: {e}")
            _append_trace("[fallback] Switching to PaymentIntent.create")
            resp = self._create_payment_intent(amount, currency, source, _append_trace)

        # Normalize response for both shapes
        obj = resp.get("object")
        if obj == "charge":
            return NormalizedPayment(
                id=resp["id"],
                amount=int(resp["amount"]),
                currency=str(resp["currency"]),
                status=str(resp["status"]),
            )
        if obj == "payment_intent":
            # Keep status as-is; payment intent might require capture
            return NormalizedPayment(
                id=resp["id"],
                amount=int(resp["amount"]),
                currency=str(resp["currency"]),
                status=str(resp.get("status", "")),
            )

        # Unknown response shape
        raise RuntimeError("unrecognized payment response")

    def _create_payment_intent(self, amount: int, currency: str, source: str, tracer) -> dict:
        # Map legacy args to v2 request
        pi_req = {
            "amount": amount,
            "currency": currency,
            "payment_method": source,
            "capture_method": "automatic",
        }
        tracer("[v2] PaymentIntent.create invoked")
        tracer(f"[v2-request] {pi_req}")
        if not hasattr(self.sdk, "PaymentIntent"):
            raise RuntimeError("PaymentIntent API not available on SDK")
        return self.sdk.PaymentIntent.create(**pi_req)  # type: ignore[attr-defined]
