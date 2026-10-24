cd /application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== CTA MAX CONFIG ==="
cat artifacts/v1.168-max/cta_native_model/config.json

echo "=== CTA MAX REGISTERED ENCODINGS ==="
grep -nE 'supported_encodings|default_encoding|weights_format|pipeline_model|SupportedArchitecture' \
  artifacts/v1.168-max/cta_max/cta_architecture_registration.py
