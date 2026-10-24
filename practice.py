cd /application1/sajjna8/rt-pzaas-cta-offers-v1

grep -nE 'queue\.stream|queue\.open_channel|CTAContext' \
artifacts/v1.168-max/maxserve_cta_extension/cta_router.py
