cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo "=== CTA REQUEST CONTEXT ===" && \
nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_context.py | sed -n '1,120p' && \
echo "=== SCHEDULER REQUEST MAPPING ===" && \
nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py | sed -n '1,45p;53,89p' && \
echo "=== HTTP CHANNEL MAPPING ===" && \
nl -ba artifacts/v1.168-max/maxserve_cta_extension/cta_router.py | sed -n '39,83p'
