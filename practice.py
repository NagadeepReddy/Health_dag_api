(
set -euo pipefail

POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

BASE=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
REPO=/application1/sajjna8/rt-pzaas-cta-offers-v1
OVERLAY="$BASE/native_batch2_cached_overlay"
CACHE="$BASE/mojo_cache_8766"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
NAME=cta-batch2-trace-8766
IMAGE=localhost/cta-max-faiss:local

test -f "$OVERLAY/cta_native_batch2_proven_server.py"
test -f "$OVERLAY/cta_native_scheduler.py"
test -f "$BASE/real_max_batch2_backend.py"
test -d "$CAND/cta_max"

"${POD[@]}" image exists "$IMAGE"

[ "$(curl --noproxy '*' -s -o /dev/null \
  -w '%{http_code}' --max-time 10 \
  http://127.0.0.1:8765/health)" = 200 ]

! ss -H -ltn '( sport = :8766 )' | grep -q .

[ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -ge 1200000 ]
[ "$(df -Pk "$BASE" | awk 'NR==2 {print $4}')" -ge 1048576 ]

if "${POD[@]}" container exists "$NAME"; then
  STATE=$("${POD[@]}" inspect --format '{{.State.Status}}' "$NAME")
  MOUNTS=$("${POD[@]}" inspect --format '{{json .Mounts}}' "$NAME")

  [ "$STATE" = exited ] || {
    echo "STOP: Container not exited"; exit 1;
  }
  [[ "$MOUNTS" == *"$OVERLAY"* ]] || {
    echo "STOP: Container identity mismatch"; exit 1;
  }
fi

mkdir -p "$CACHE"

if "${POD[@]}" container exists "$NAME"; then
  "${POD[@]}" rm "$NAME"
fi

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
  -v "$CACHE:/opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  "$IMAGE" \
  -B /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_batch2_proven_server.py

echo "ISOLATED SERVER: RECREATED"
echo "MOJO CACHE: WRITABLE UNDER APPLICATION1"
echo "ORIGINAL DS: UNCHANGED"
echo "ORIGINAL MAX HTTP:"
curl --noproxy '*' -s -o /dev/null \
  -w '%{http_code}\n' --max-time 10 \
  http://127.0.0.1:8765/health
)
