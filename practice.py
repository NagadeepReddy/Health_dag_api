C=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension
B=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

echo "=== WORKING CTA QUEUE COMPATIBILITY ==="
if [ -f "$C/cta_queue_compat.py" ]; then
  nl -ba "$C/cta_queue_compat.py" | head -130
else
  echo "CTA compatibility file not found"
fi

echo "=== BPLAN QUEUE PATCHES AND INSTALLATION ==="
grep -nE 'queue_compat|ZmqPullSocket|_safe_get_nowait|response_worker|install' \
  "$B/bplan_native_launcher.py" \
  "$B/bplan_http_pipeline.py" \
  "$B/bplan_spawn_worker.py" 2>/dev/null | head -65

echo "=== CURRENT BPLAN WORKER FAILURE ==="
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)
ID=$("${P[@]}" ps --format '{{.ID}} {{.Command}}' | awk '/bplan_native_launcher/ {print $1; exit}')

if [ -n "$ID" ]; then
  "${P[@]}" logs --tail 700 "$ID" 2>&1 |
    grep -iE -C 5 'worker failed|missing required|traceback|exception|scheduler failed|zmq.*error|typeerror|keyerror' |
    tail -100
else
  echo "BPLAN server container not running"
fi
