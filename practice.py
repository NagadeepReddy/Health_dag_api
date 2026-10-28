cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -RnE \
'_cta_wait_for_healthy_worker|response_worker\(|__aenter__|_background_tasks|CTA RECEIVER' \
artifacts/v1.168-max/maxserve_cta_extension \
--include='*.py' \
--exclude='*.bak'
