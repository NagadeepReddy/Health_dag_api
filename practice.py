cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
OVERLAY="$DEV/native_batch2_minimal_overlay"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/postman_native_max_live.log"

test -f "$OVERLAY/cta_native_batch2_proven_server.py"
test -d "$CAND"

RAM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
test "$RAM" -ge 16777216 || {
  echo "STOP: Available memory below 16 GiB"
  exit 1
}

python3 - "$OVERLAY/cta_native_batch2_proven_server.py" <<'PY'
from pathlib import Path
import sys
source = Path(sys.argv[1]).read_text()
assert 'host="127.0.0.1"' in source
assert "port=8765" in source
assert "disable_telemetry=True" in source
print("LOCALHOST-ONLY NATIVE SERVER CONFIG: PASS")
PY

echo "STARTING NATIVE MAX SERVE FOR POSTMAN"

TMPDIR="$DEV" timeout -k 15s 900s podman \
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
  -u -B /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_batch2_proven_server.py \
  2>&1 | tee "$LOG"
SH
