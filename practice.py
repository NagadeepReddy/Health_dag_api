cd /application1/sajjna8/rt-pzaas-cta-offers-v1

echo "=== CTA NATIVE SCHEDULER ==="
sed -n '1,150p' artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py

echo "=== CTA SCHEDULER FACTORY ==="
sed -n '1,110p' artifacts/v1.168-max/maxserve_cta_extension/cta_scheduler_factory.py

echo "=== CTA ROUTE CONNECTION ==="
sed -n '1,65p' artifacts/v1.168-max/maxserve_cta_extension/cta_router.py

echo "CTA LIFECYCLE INTEGRATION REVIEW COMPLETE"
