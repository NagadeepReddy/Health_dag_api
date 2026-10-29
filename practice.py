cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
INPUT=artifacts/v1.168-max/cta_native_adjusted_sanity_input.json
LOG="$DEV/real_cta_json_batch2_adapter_e2e.log"

test -s "$DEV/native_batch2/cta_worker_adapter.py"
test -s "$DEV/real_max_batch2_backend.py"
test -s "$INPUT"
test -d "$CAND"
test ! -e "$LOG" || { echo "STOP: Preserve existing log"; exit 1; }

AVAILABLE_KB=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
if [ "$AVAILABLE_KB" -lt 14680064 ]; then
  echo "STOP: Less than 14 GiB available RAM. Do not start MAX."
  exit 1
fi

echo "=== REAL CTA JSON BATCH-2 ADAPTER EXECUTION ==="

set +e
timeout -k 15s 420s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 12g --cpus 4 --pids-limit 256 \
  --tmpfs /tmp:rw,size=512m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONUNBUFFERED=1 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH="/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max:/batch2:$CAND" \
  -e modelId=rt-pzaas-cta-offers-v1 \
  -e expThrottleLabel=T \
  -v "$PWD:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -B - > "$LOG" 2>&1 <<'PY'
import importlib.util
import json
import numpy as np
from pathlib import Path
from pipeline import pipeline as CTA
from cta_max.live_cta_pipeline_bridge import attach_max

p = Path("/batch2/native_batch2/cta_worker_adapter.py")
spec = importlib.util.spec_from_file_location("cta_batch_adapter_dev", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

body = json.loads(source.read_text())
assert isinstance(body, dict)

adapter = module.CTAWorkerAdapter(CTA, attach_max)

print("REAL CTA JSON BATCH ADAPTER: START", flush=True)
responses = adapter.predict_batch([body, json.loads(source.read_text())])

assert isinstance(responses, list) and len(responses) == 2
assert all(isinstance(x, dict) for x in responses)

print("TWO CTA JSON RESPONSES: PASS", flush=True)
print("CTA RESPONSE ROOT KEYS:", [sorted(x.keys()) for x in responses])
print("DUPLICATE REQUEST RESPONSE PARITY:",
      "PASS" if responses[0] == responses[1] else "DIFFERENT")
assert responses[0] == responses[1]
print("REAL CTA JSON BATCH ADAPTER E2E: PASS", flush=True)
PY

RC=$?
set -e

echo "=== RESULTS ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
tail -55 "$LOG"

if [ "$RC" -eq 0 ] &&
   grep -q 'REAL CTA JSON BATCH ADAPTER E2E: PASS' "$LOG"; then
  echo "DEVELOPMENT JSON BATCH ADAPTER: PASS"
else
  echo "DEVELOPMENT JSON BATCH ADAPTER: NOT VALIDATED"
fi

echo "ORIGINAL DS CODE: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
exit "$RC"
SH
