(
set -e

POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

BASE=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1
OVERLAY="$BASE/native_batch2_cached_overlay"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
IMAGE=localhost/cta-max-faiss:local
NAME=cta-batch2-trace-8766

[ -f "$OVERLAY/cta_native_batch2_proven_server.py" ] || {
  echo "STOP: Test launcher missing"; exit 1;
}
[ -f "$OVERLAY/cta_native_scheduler.py" ] || {
  echo "STOP: Scheduler missing"; exit 1;
}
[ -f "$BASE/real_max_batch2_backend.py" ] || {
  echo "STOP: MAX backend missing"; exit 1;
}
[ -d "$CAND/cta_max" ] || {
  echo "STOP: MAX candidate missing"; exit 1;
}

"${POD[@]}" image exists "$IMAGE" || {
  echo "STOP: Existing development image missing"; exit 1;
}

"${POD[@]}" container exists "$NAME" && {
  echo "STOP: Test container already exists"; exit 1;
}

[ "$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 10 http://127.0.0.1:8765/health)" = 200 ] || {
  echo "STOP: Original MAX unhealthy"; exit 1;
}

! ss -H -ltn '( sport = :8766 )' | grep -q . || {
  echo "STOP: Port 8766 occupied"; exit 1;
}

MEM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
[ "$MEM" -ge 1200000 ] || {
  echo "STOP: Insufficient available memory"; exit 1;
}

"${POD[@]}" run -d \
  --name "$NAME" \
  --network host \
  --read-only \
  --memory 1700m \
  --memory-swap 1700m \
  --tmpfs /tmp:rw,exec,size=1024m \
  --tmpfs /root:rw,size=16m \
  --tmpfs /run:rw,size=64m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace:/workspace/artifacts/v1.168-max:/batch2 \
  -v "$REPO:/workspace:ro" \
  -v "$OVERLAY:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
  -v "$CAND:/batch2:ro" \
  -v "$BASE/real_max_batch2_backend.py:/batch2/real_max_batch2_backend.py:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" \
  -B /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_batch2_proven_server.py

echo "ISOLATED SERVER: LAUNCH REQUESTED"
echo "ORIGINAL MAX: UNCHANGED"
echo "ORIGINAL DS: UNCHANGED"
)
