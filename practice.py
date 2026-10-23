cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_worker_registration.py | head -110
