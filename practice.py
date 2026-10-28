cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -C 3 -E '"transactionMetadata"|"best_modelId"|"modelId"' \
artifacts/v1.168-max/cta_native_adjusted_sanity_input.json \
artifacts/v1.168-max/maxserve_cta_extension/cta_router.py
