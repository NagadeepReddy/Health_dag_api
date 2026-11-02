CTA=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

echo "=== WORKER ADAPTER ==="
grep -n -A 22 -E 'def (__init__|predict|predict_batch)\(' \
  "$CTA/cta_worker_adapter.py"

echo "=== SCHEDULER FACTORY ==="
grep -n -A 18 -E 'def |class ' \
  "$CTA/cta_native_scheduler_factory.py"

echo "=== ROUTER REGISTRATION ==="
grep -n -A 12 -E 'register|def |class ' \
  "$CTA/cta_router.py" | head -100
