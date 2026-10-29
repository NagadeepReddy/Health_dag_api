cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/real_cta_json_batch2_candidate_graph.log"

test -s "$DEV/real_max_batch2_backend.py"
test -s "$DEV/native_batch2/cta_worker_adapter.py"
test -s "$CAND/cta_max/grecbase_fusion_full_head_72_max.py"
test ! -e "$LOG" || {
  echo "STOP: Log already exists"
  exit 1
}

MEM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

test "$MEM" -ge 14680064 || {
  echo "STOP: RAM below safety threshold"
  exit 1
}
test "$DISK" -ge 20971520 || {
  echo "STOP: Disk below safety threshold"
  exit 1
}

set +e
timeout -k 15s 420s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 12g --cpus 4 --pids-limit 256 \
  --tmpfs /tmp:rw,size=512m \
  --tmpfs /root:rw,size=64m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e modelId=rt-pzaas-cta-offers-v1 \
  -e expThrottleLabel=T \
  -e PYTHONPATH="$CAND:/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max:/batch2" \
  -v "$PWD:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -B - > "$LOG" 2>&1 <<'PY'
import json
import sys
import importlib
import importlib.util
from pathlib import Path

candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)
original_max = Path(
    "/workspace/artifacts/v1.168-max/cta_max"
)

import cta_max

paths = cta_max.__path__

if str(candidate) in paths:
    paths.remove(str(candidate))
paths.insert(0, str(candidate))

if str(original_max) not in paths:
    paths.append(str(original_max))

name = "cta_max.grecbase_fusion_full_head_72_max"
expected = candidate / "grecbase_fusion_full_head_72_max.py"

if name in sys.modules:
    loaded = Path(sys.modules[name].__file__).resolve()
    assert loaded == expected.resolve(), (
        f"STOP: Wrong graph already loaded: {loaded}"
    )

graph = importlib.import_module(name)

assert Path(graph.__file__).resolve() == expected.resolve(), (
    f"STOP: Wrong MAX graph: {graph.__file__}"
)

print("BATCH-2 CANDIDATE GRAPH: PASS", flush=True)

from pipeline import pipeline as CTA
from cta_max.live_cta_pipeline_bridge import attach_max
from cta_max.run_batch2_contract import pack_two_requests

assert callable(pack_two_requests)
print("BATCH CONTRACT: PASS", flush=True)

file = Path("/batch2/native_batch2/cta_worker_adapter.py")
spec = importlib.util.spec_from_file_location(
    "cta_batch_adapter_dev", file
)
assert spec and spec.loader

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

input_file = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

body = json.loads(input_file.read_text())
adapter = module.CTAWorkerAdapter(CTA, attach_max)

print("REAL CTA JSON BATCH-2: START", flush=True)

responses = adapter.predict_batch([body, body])

assert isinstance(responses, list) and len(responses) == 2

for i, response in enumerate(responses, 1):
    assert isinstance(response, dict)
    prediction = response["jsonData"]["prediction"]
    assert isinstance(prediction, dict)
    print(f"CTA RESPONSE {i}: PASS", flush=True)

print("DEVELOPMENT JSON BATCH-2 E2E: PASS", flush=True)
PY

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
tail -55 "$LOG"

if [ "$RC" -eq 0 ] &&
   grep -q 'DEVELOPMENT JSON BATCH-2 E2E: PASS' "$LOG"; then
  echo "JSON BATCH-2: PASS"
else
  echo "JSON BATCH-2: NOT VALIDATED"
fi

echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
exit "$RC"
SH
