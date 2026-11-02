STAGE=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031

echo "=== NATIVE MAX SERVE FILES ==="
find "$STAGE" -type f \
  \( -name '*native*launcher*.py' \
  -o -name '*native*scheduler*.py' \
  -o -name '*scheduler*factory*.py' \
  -o -name '*native*http*.py' \
  -o -name '*architecture*registration*.py' \
  -o -name 'cta_worker_adapter.py' \) \
  -not -path '*/__pycache__/*' | sort

echo "=== BPLAN ADAPTER ==="
test -f /application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev/bplan_max_model_adapter.py \
  && echo "BPLAN ADAPTER: READY"
