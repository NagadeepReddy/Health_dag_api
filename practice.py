cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/real_cta_json_batch2_after_bridge.log"
INPUT=artifacts/v1.168-max/cta_native_adjusted_sanity_input.json

test -s "$DEV/native_batch2/cta_worker_adapter.py"
test -s "$DEV/real_max_batch2_backend.py"
test -s "$CAND/cta_max/run_batch2_contract.py"
test -s "$INPUT"
test ! -e "$LOG" || {
  echo "STOP: Test log already exists"
  exit 1
}

MEM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

test "$MEM" -ge 14680064 || {
  echo "STOP: Insufficient available RAM"
  exit 1
}
test "$DISK" -ge 20971520 || {
  echo "STOP: Insufficient disk space"
  exit 1
}

echo "=== CTA REAL JSON BATCH-2 ==="

set +e
timeout -k 15s 420s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none --read-only \
  --memory 12g --cpus 4 --pids-limit 256 \
  --tmpfs /tmp:rw,size=512m \
  --tmpfs /root:rw,size=64m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e modelId=rt-pzaas-cta-offers-v1 \
  -e expThrottleLabel=T \
  -e PYTHONPATH="/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max:/batch2:$CAND" \
  -v "$PWD:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -B - > "$LOG" 2>&1 <<'PY'
import json
import importlib.util
from pathlib import Path

import cta_max

candidate = (
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)

if candidate not in cta_max.__path__:
    cta_max.__path__.append(candidate)

from cta_max.run_batch2_contract import pack_two_requests
assert callable(pack_two_requests)
print("BATCH CONTRACT IMPORT: PASS", flush=True)

from pipeline import pipeline as CTA
from cta_max.live_cta_pipeline_bridge import attach_max

adapter_file = Path(
    "/batch2/native_batch2/cta_worker_adapter.py"
)

spec = importlib.util.spec_from_file_location(
    "cta_batch_adapter_dev", adapter_file
)
assert spec is not None and spec.loader is not None

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert callable(
    getattr(module.CTAWorkerAdapter, "predict_batch", None)
)
print("BATCH ADAPTER IMPORT: PASS", flush=True)

input_file = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

body = json.loads(input_file.read_text())
adapter = module.CTAWorkerAdapter(CTA, attach_max)

print("REAL CTA JSON BATCH-2: START", flush=True)

responses = adapter.predict_batch([body, body])

assert isinstance(responses, list)
assert len(responses) == 2

for i, response in enumerate(responses):
    assert isinstance(response, dict)
    assert isinstance(response.get("jsonData"), dict)
    assert isinstance(
        response["jsonData"].get("prediction"), dict
    )
    print(
        f"CTA RESPONSE {i+1}: PASS",
        sorted(response["jsonData"]["prediction"]),
        flush=True
    )

print("TWO REAL CTA JSON RESPONSES: PASS", flush=True)
print("DEVELOPMENT MAX JSON BATCH E2E: PASS", flush=True)
PY

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
tail -55 "$LOG"

if [ "$RC" -eq 0 ] &&
   grep -q 'DEVELOPMENT MAX JSON BATCH E2E: PASS' "$LOG"; then
  echo "JSON BATCH-2 VALIDATION: PASS"
else
  echo "JSON BATCH-2 VALIDATION: NOT PASSED"
fi

echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"

exit "$RC"
SH
