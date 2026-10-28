cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
echo '=== MAX ENGINE LOAD ===' && \
nl -ba artifacts/v1.168-max/cta_max/run_live_max_inference.py | sed -n '175,210p' && \
echo '=== CTA MAX BRIDGE ===' && \
nl -ba artifacts/v1.168-max/cta_max/live_cta_pipeline_bridge.py | sed -n '1,90p'
