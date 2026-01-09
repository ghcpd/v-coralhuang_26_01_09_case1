# PaymentClient migration

This small repo demonstrates migrating a payment client from a legacy Charges API to the newer PaymentIntent API, with runtime fallback.

## Original failure modes
- The baseline `PaymentClient` called `sdk.Charge.create(...)` only. That breaks when:
  - The runtime SDK only exposes `PaymentIntent` (no `Charge` attribute) and AttributeError occurs, or
  - The legacy SDK's backend removes the Charges endpoint at a certain `VERSION`, causing `RuntimeError("endpoint removed")` at runtime.

## Fail → Pass testing strategy
1. I wrote three tests that express the desired behavior (they initially fail against the baseline):
   - `test_legacy_charge_works` — verifies legacy Charges still work when the endpoint exists.
   - `test_legacy_endpoint_removed_fallback` — simulates a runtime `RuntimeError` and asserts an automatic fallback to `PaymentIntent`.
   - `test_v2_payment_intent_only` — verifies the client works when only `PaymentIntent` exists.
2. I updated `PaymentClient` to:
   - Detect whether `Charge` is present and attempt it first when available.
   - Catch `RuntimeError` from a removed endpoint and automatically retry via `PaymentIntent` if available.
   - If `Charge` is not present, call `PaymentIntent` directly.
   - Normalize responses from both APIs to a common `NormalizedPayment` dataclass.

## How fallback and migration work
- Request mapping: the legacy `source` parameter is mapped to `payment_method` for `PaymentIntent`.
- `capture_method` is set to `"automatic"` for new PaymentIntent requests.
- Runtime selection relies only on attribute checks and exception handling (no env vars or feature flags).
- The client logs a small runtime trace in `artifacts/runtime_trace.txt` so reviewers can see which path ran.

## How to run and evaluate
1. Run the included script from PowerShell in the repo root:

   ./run_tests

2. After the script completes successfully, open:
   - `ARTIFACTS.md` — a short human-friendly summary showing the three tests as PASS.
   - `artifacts/runtime_trace.txt` — plain-text evidence of the runtime path taken (legacy, error, fallback, v2).

That's it — the tests and the artifacts let a reviewer validate the migration without deep code inspection.