B=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev
C=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension

for f in "$C/cta_router.py" "$B/bplan_router.py" "$C/cta_context.py" "$B/bplan_context.py"; do
  echo "========== $f =========="
  if [ -f "$f" ]; then
    nl -ba "$f" | head -100
  else
    echo "FILE NOT FOUND"
  fi
done
