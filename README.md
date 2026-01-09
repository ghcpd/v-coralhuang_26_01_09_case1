# PaymentClient migration — README

Summary
- The baseline `PaymentClient` only used the legacy `Charge.create` API and would fail
  when the backend removed that endpoint or when running against the v2 SDK.

What I changed
- Added runtime-detection + exception-handling fallback from `Charge.create` to
  `PaymentIntent.create`.
- Normalized responses from both schemas into `NormalizedPayment`.
- Emitted a plain `artifacts/runtime_trace.txt` during execution so reviewers can
  see which code path was taken.
- Added tests that reproduce the failure modes and verify the fallback.

Fail → Pass strategy
1. Write failing tests that prove legacy behavior, endpoint-removal fallback, and
   v2-only operation.
2. Implement runtime-safe detection and mapping (`source -> payment_method`,
   `capture_method="automatic"`).
3. Normalize responses and produce human-friendly artifacts.

How fallback and migration work (brief)
- PaymentClient attempts `sdk.Charge.create(...)` first.
- If that call raises `RuntimeError("endpoint removed")` or the SDK lacks
  `Charge`, the client maps the request to the v2 contract and calls
  `sdk.PaymentIntent.create(..., payment_method=<source>, capture_method="automatic")`.

How to run
- On Windows PowerShell (workspace root):
  ./run_tests

What to inspect (for quick review)
- `ARTIFACTS.md` — test summary and request-mapping evidence
- `artifacts/runtime_trace.txt` — runtime path taken during tests
- `tests/test_payment_client.py` — the three required tests
