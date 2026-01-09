# Agent Migration Artifacts

## Test Coverage Summary
- test_legacy_charge_works: PASS
- test_legacy_endpoint_removed_fallback: PASS
- test_v2_payment_intent_only: PASS

## Runtime Behavior Evidence
- Legacy endpoint removal observed
- Automatic fallback to PaymentIntent confirmed

## Request Mapping Evidence
- source -> payment_method
- capture_method="automatic" applied

## Test Execution Details

All three mandatory tests passed successfully:

1. **test_legacy_charge_works**: Validated that the legacy Charges API still works when the endpoint is available in older SDK versions.

2. **test_legacy_endpoint_removed_fallback**: Confirmed that when the Charges endpoint is removed at runtime (SDK VERSION >= "2022-11-15"), the client automatically catches the RuntimeError and falls back to the PaymentIntent API.

3. **test_v2_payment_intent_only**: Verified that the client works seamlessly with modern SDKs that only expose the PaymentIntent API (no Charge API present).

## Runtime Trace Location

See `artifacts/runtime_trace.txt` for detailed execution flow evidence.

## Key Implementation Details

- **Capability Detection**: Uses `hasattr(sdk, 'Charge')` to check for legacy API availability
- **Exception Handling**: Catches `RuntimeError("endpoint removed")` and triggers fallback
- **Request Mapping**: Automatically maps `source` 鈫?`payment_method` and adds `capture_method="automatic"`
- **Response Normalization**: Both Charge and PaymentIntent responses are normalized to consistent `NormalizedPayment` schema

## Evaluation Commands

`powershell
# Run all tests
.\run_tests.ps1

# View runtime trace
cat artifacts\runtime_trace.txt

# View this summary
cat ARTIFACTS.md
`

All deliverables are present and tests pass.
