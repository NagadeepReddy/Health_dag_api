cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
OVERLAY="$DEV/native_batch2_minimal_overlay"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate

test -f "$OVERLAY/cta_native_batch2_proven_server.py"
test -f "$OVERLAY/cta_native_scheduler.py"

if curl --noproxy '*' -fsS --connect-timeout 3 \
  http://127.0.0.1:8765/health >/dev/null 2>&1; then
  echo "NATIVE MAX SERVER: ALREADY RUNNING"
else
  echo "STARTING NATIVE MAX SERVER WITHOUT TIMEOUT"

  TMPDIR="$DEV" podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm -i --pull=never \
    --network host --read-only \
    --memory 14g --memory-swap 14g \
    --cpus 4 --pids-limit 256 \
    --tmpfs /tmp:rw,size=2g \
    --tmpfs /root:rw,size=64m \
    --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=2g,mode=1777 \
    -v "$PWD:/workspace:ro" \
    -v "$OVERLAY:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
    -v "$DEV:/batch2:ro" \
    -v "$CAND:$CAND:ro" \
    -w /workspace \
    -e HOME=/tmp \
    -e TMPDIR=/tmp \
    -e XDG_CACHE_HOME=/tmp \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e PYTHONUNBUFFERED=1 \
    -e modelId=rt-pzaas-cta-offers-v1 \
    -e expThrottleLabel=T \
    -e PYTHONPATH="$CAND:/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max:/workspace" \
    --entrypoint /opt/venv/bin/python \
    localhost/cta-max-faiss:local \
    -u -B /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_batch2_proven_server.py
fi
SH
