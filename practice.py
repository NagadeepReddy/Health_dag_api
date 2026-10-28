cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== CTA SCHEDULER QUEUE CONFIGURATION ===" && \
nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_scheduler_factory.py | sed -n '1,125p' && \
echo "=== CTA TEST QUEUE INITIALIZATION ===" && \
nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py | sed -n '1,65p'
