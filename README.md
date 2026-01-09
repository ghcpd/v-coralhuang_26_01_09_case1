# PaymentClient Migration

## Original failure modes
- The baseline `PaymentClient` only used the legacy `Charge.create` API.
- If the Charges endpoint was removed at runtime (simulated by raising `RuntimeError("endpoint removed")`), the client crashed and payments failed.
- If the SDK only supported the newer `PaymentIntent` API, the client crashed with `AttributeError`.

## Testing strategy (fail → pass)
1. Added three tests that initially failed against the baseline:
   - `test_legacy_charge_works` — verifies legacy Charges still work.
   - `test_legacy_endpoint_removed_fallback` — simulates endpoint removal and verifies automatic fallback to `PaymentIntent`.
   - `test_v2_payment_intent_only` — verifies the client works when only `PaymentIntent` exists.
2. Implemented runtime tracing (written to `artifacts/runtime_trace.txt`) so tests can assert which execution path occurred.
3. Implemented fallback and request/response normalization in `PaymentClient.pay` so all tests pass.

## How fallback and migration work
- The client first tries the legacy `Charge.create` call.
- If `AttributeError` (no Charge API) or `RuntimeError("endpoint removed")` occurs, the client falls back to `PaymentIntent.create`.
- When using `PaymentIntent`, the client maps the legacy `source` parameter to `payment_method` and sets `capture_method` to `automatic`.
- The method normalizes both response shapes to a single `NormalizedPayment` dataclass.
- Each runtime decision is appended to `artifacts/runtime_trace.txt` for human evaluation.

## How to run and evaluate
1. Run `./run_tests` (requires a POSIX shell) — it creates a virtual environment, installs `pytest`, and runs the tests.
2. Open `ARTIFACTS.md` to see the test coverage summary.
3. Open `artifacts/runtime_trace.txt` to see the runtime execution trace and confirm fallback behavior.

