CTA=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
BPLAN=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== CTA NATIVE SERVING COMPONENTS ==="
find "$CTA" -type f \
  \( -name 'cta_native_launcher.py' \
  -o -name 'cta_native_scheduler_factory.py' \
  -o -name 'cta_native_scheduler.py' \
  -o -name 'cta_worker_adapter.py' \
  -o -name 'cta_router.py' \) \
  -print

echo "=== NATIVE SERVING INTERFACES ==="
find "$CTA" -type f \
  \( -name 'cta_native_launcher.py' \
  -o -name 'cta_native_scheduler_factory.py' \
  -o -name 'cta_worker_adapter.py' \
  -o -name 'cta_router.py' \) \
  -exec grep -HnE '^(class |def |    def )|register|SchedulerFactory' {} \; \
  | head -90

echo "=== BPLAN ISOLATED ADAPTER ==="
test -f "$BPLAN/bplan_max_dev/bplan_max_model_adapter.py" && \
echo "BPLAN MODEL ADAPTER: PRESENT"
