cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
sed -n '1,180p' artifacts/v1.168-max/maxserve_cta_extension/cta_architecture_registration.py && \
echo '=== CTA MODEL CONFIG ===' && \
cat artifacts/v1.168-max/cta_native_model/config.json
