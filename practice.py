cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

sed -n '1,220p' \
artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py
