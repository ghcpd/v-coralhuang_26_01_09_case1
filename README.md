# PaymentClient Migration

🔧 Summary

- The baseline `PaymentClient` only used the legacy `Charge.create` API.
- After SDK/backend upgrades the legacy endpoint can be removed at runtime and raise `RuntimeError("endpoint removed")`.

💥 Original failure modes

- `PaymentClient.pay` crashed or could not operate when:
  - the SDK removed/disabled the `/charges` endpoint at runtime, raising `RuntimeError`.
  - the environment only had the v2 `PaymentIntent.create` API (no `Charge`).

✅ Fail → Pass testing strategy

- I first added tests that exercise:
  - legacy Charges API (`test_legacy_charge_works`)
  - runtime removal of the legacy endpoint with automatic fallback (`test_legacy_endpoint_removed_fallback`)
  - SDKs that only support PaymentIntent (`test_v2_payment_intent_only`)

- Tests were written to assert normalized responses and also to verify the runtime trace written to `artifacts/runtime_trace.txt`.

🔧 How fallback & migration work

- `PaymentClient.pay(...)` now:
  1. Attempts the legacy flow if `sdk.Charge` exists and logs the attempt.
  2. If a `RuntimeError("endpoint removed")` is raised, it logs the error and falls back to `sdk.PaymentIntent.create(...)` if available.
  3. If no `Charge` exists but `PaymentIntent` does, it will call `PaymentIntent` directly.

- Request mapping: `source` → `payment_method`, and `capture_method="automatic"` is applied for v2 requests.
- Response normalization:
  - For legacy Charge responses, `id` is used as the normalized id.
  - For PaymentIntent responses, `latest_charge` (when present) is used as the normalized id, otherwise `id`.

📁 Artifacts

- `artifacts/runtime_trace.txt` — runtime trace of what path was taken during the tests
- `ARTIFACTS.md` — summary for human evaluation (generated after tests run)

▶️ How to run

On Unix-like systems (or Git Bash on Windows):

```bash
./run_tests
```

On Windows PowerShell:

```powershell
.\




The scripts will create a virtual environment, install `pytest`, run the tests, and write the artifacts.```un_tests.ps1