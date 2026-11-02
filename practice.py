CTA=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension
BPLAN=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== BPLAN ADAPTER ==="
test -f "$BPLAN/bplan_max_dev/bplan_max_model_adapter.py" && echo "PASS"

echo "=== NATIVE REGISTRATION ==="
sed -n '1,150p' "$CTA/cta_architecture_registration.py"

echo "=== SCHEDULER FACTORY ==="
sed -n '1,160p' "$CTA/cta_scheduler_factory.py"

echo "=== NATIVE LAUNCHER ==="
sed -n '1,130p' "$CTA/cta_native_launcher.py"

echo "=== HTTP ENTRY INTERFACES ==="
grep -nE '^(class |def |async def |    def )|register|route|scheduler' \
"$CTA/cta_native_http_entry.py" | head -65
