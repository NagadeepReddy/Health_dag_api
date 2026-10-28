cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -Rn -C 3 --include='*.py' 'modelId' \
artifacts/v1.168/core-artifact \
artifacts/v1.168-max/maxserve_cta_extension | head -100
