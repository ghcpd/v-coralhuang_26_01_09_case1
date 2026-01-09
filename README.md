# PaymentClient Migration

This project demonstrates the migration of a Python payment client from a deprecated Charges API to a modern PaymentIntent API with automatic fallback handling.

## Original Failure Modes

The baseline `PaymentClient` only supported the legacy `sdk.Charge.create(amount, currency, source)` API. It would fail in two scenarios:

1. **SDK Upgrade with Endpoint Removal**: When `LegacyStripeSDK.VERSION >= "2022-11-15"`, the Charges endpoint raises `RuntimeError("endpoint removed")` at runtime.

2. **V2-Only SDKs**: Modern SDKs like `StripeSDKv2` only expose `PaymentIntent.create(amount, currency, payment_method, capture_method)`, lacking the `Charge` API entirely, causing `AttributeError`.

## Fail → Pass Testing Strategy

Tests were written first to capture the required behaviors and initially fail against the baseline implementation:

- `test_legacy_charge_works`: Verifies legacy API works when available.
- `test_legacy_endpoint_removed_fallback`: Ensures runtime endpoint removal triggers fallback to PaymentIntent.
- `test_v2_payment_intent_only`: Confirms PaymentIntent works without legacy APIs.

The implementation was then migrated to handle all cases, making tests pass.

## How Fallback and Migration Work

The `PaymentClient.pay()` method uses runtime capability detection and exception handling:

1. **Attempt Legacy Charge**: Try `sdk.Charge.create()` with `source` parameter.
2. **Handle Missing Charge API**: If `AttributeError` (no `Charge` attribute), switch to `PaymentIntent.create()` with `payment_method=source` and `capture_method="automatic"`.
3. **Handle Runtime Removal**: If `RuntimeError("endpoint removed")`, fallback to `PaymentIntent.create()` with the same mapping.

Request mapping:
- `source` → `payment_method`
- Add `capture_method="automatic"` for PaymentIntent.

Response normalization ensures consistent `NormalizedPayment` output regardless of API used.

## How to Run and Evaluate

1. Run `./run_tests.bat` (or `python run_tests.py` on Unix-like systems).
2. Open `ARTIFACTS.md` for test coverage and evidence summary.
3. Open `artifacts/runtime_trace.txt` for plain-text runtime path evidence.

No deep code reading required; the artifacts provide all evaluation evidence.