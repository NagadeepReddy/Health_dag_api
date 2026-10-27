cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
git diff --check -- artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py && echo "CHANGE CHECK: PASS"
