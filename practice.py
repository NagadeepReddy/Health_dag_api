cd /application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== CTA ARCHITECTURE REGISTRATION ==="

sed -n '1,150p' \
artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py
