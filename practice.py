cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== HTTP PIPELINE REMAINING CODE ===" && \
nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_http_pipeline.py | sed -n '60,150p' && \
echo "=== PREVIOUS RESPONSE RECEIVER LOGS ===" && \
grep -nE 'CTA RECEIVER|CTA HTTP QUEUE ITEM|CTA HTTP FANOUT|CTA NATIVE HTTP STATUS|response.worker|response_worker' \
/application1/cta_env_e2e_1028.log | head -25
