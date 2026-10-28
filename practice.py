cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -C 5 -E 'modelId|sanity_input|request\.json|payload|predict|_cta_adapter' \
  artifacts/v1.168-max/maxserve_cta_extension/cta_router.py \
  artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py \
  artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py \
  artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py \
  | head -180
