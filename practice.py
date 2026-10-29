cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
RUNNER="$DEV/native_http_batch2_healthfix_runner.py"
OVERLAY="$DEV/native_batch2_minimal_overlay"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/native_http_batch2_healthfix_retry.log"

python3 - "$RUNNER" <<'PY'
import ast, sys
from pathlib import Path

p = Path(sys.argv[1])
assert p.is_file() and not p.is_symlink(), "STOP: Runner missing or linked"
src = p.read_text()
ast.parse(src)

assert 'json.loads(raw) if raw.strip() else {}' in src, \
    "STOP: Corrected health check not present"
assert "NATIVE HTTP REAL MAX BATCH-2: PASS" in src, \
    "STOP: Batch validation missing"

print("EXISTING CORRECTED RUNNER: PASS")
PY

test -f "$OVERLAY/cta_native_batch2_proven_server.py"
test -d "$CAND"

RAM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
test "$RAM" -ge 16777216 || {
  echo "STOP: Available RAM below 16 GiB"
  exit 1
}

echo "MEMORY SAFETY: PASS"

set +e
TMPDIR="$DEV" timeout -k 15s 330s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network none --read-only \
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
  -u -B /batch2/native_http_batch2_healthfix_runner.py \
  > "$LOG" 2>&1
RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
grep -E 'PASS|STOP:|Traceback|Error|HTTP STATUS|BATCH EXECUTIONS' "$LOG" | tail -30 || true

if [ "$RC" -eq 0 ] &&
   grep -q 'NATIVE HTTP REAL MAX BATCH-2: PASS' "$LOG"; then
  echo "FINAL NATIVE BATCH-2: PASS"
else
  echo "FINAL NATIVE BATCH-2: NOT VERIFIED"
fi

echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
SH
