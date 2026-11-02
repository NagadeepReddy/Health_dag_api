CTA=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension
BPLAN=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

echo "=== CTA NATIVE HTTP ROUTES ==="
sed -n '1,165p' "$CTA/cta_router.py"

echo "=== CTA HTTP ENTRY ==="
sed -n '1,105p' "$CTA/cta_native_http_entry.py"

echo "=== BPLAN LAUNCHER ==="
sed -n '1,145p' "$BPLAN/bplan_native_serve_dev/bplan_native_launcher.py"

echo "=== BPLAN SERVING CONFIG FILES ==="
find "$BPLAN" -maxdepth 3 -type f \
  \( -name '*.yaml' -o -name '*.toml' -o -name '*config*.json' \) \
  | head -25
