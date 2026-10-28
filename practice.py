cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -n -C 6 -E 'predict|body|payload|transactionMetadata|modelId' \
artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py | head -110
