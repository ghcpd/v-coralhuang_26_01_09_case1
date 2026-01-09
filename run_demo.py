from pathlib import Path
import fake_stripe_legacy
import fake_stripe_v2
from payment_client import PaymentClient

ART = Path("artifacts/runtime_trace.txt")
if ART.exists():
    ART.unlink()

print("-- legacy working --")
sdk = fake_stripe_legacy.LegacyStripeSDK
client = PaymentClient(sdk=sdk)
r = client.pay(amount=100, currency="usd", source="tok_visa")
print(r)

print("-- legacy endpoint removed + fallback in same SDK --")
sdk = fake_stripe_legacy.LegacyStripeSDK
sdk.VERSION = "2022-11-15"
sdk.PaymentIntent = fake_stripe_v2.PaymentIntent
client = PaymentClient(sdk=sdk)
r = client.pay(amount=200, currency="eur", source="tok_amex")
print(r)

print("-- v2 only --")
sdk = fake_stripe_v2.StripeSDKv2
client = PaymentClient(sdk=sdk)
r = client.pay(amount=300, currency="gbp", source="tok_mastercard")
print(r)

print('\nRuntime trace:')
print(ART.read_text())
