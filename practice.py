cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/real_cta_scheduler_batch2_e2e.log"

test -s "$DEV/native_batch2/cta_native_scheduler.py"
test -s "$DEV/native_batch2/cta_worker_adapter.py"
test -s "$DEV/real_max_batch2_backend.py"
test -s "$CAND/cta_max/grecbase_fusion_full_head_72_max.py"
test ! -e "$LOG" || {
  echo "STOP: Log already exists"
  exit 1
}

MEM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

test "$MEM" -ge 14680064 || {
  echo "STOP: Insufficient available RAM"
  exit 1
}
test "$DISK" -ge 20971520 || {
  echo "STOP: Insufficient available disk"
  exit 1
}

set +e
TMPDIR="$DEV" timeout -k 15s 420s podman \
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
import importlib
from pathlib import Path
from queue import Queue, Empty
from types import SimpleNamespace

import cta_max

candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)
original = Path(
    "/workspace/artifacts/v1.168-max/cta_max"
)

paths = cta_max.__path__
if str(candidate) in paths:
    paths.remove(str(candidate))
paths.insert(0, str(candidate))
if str(original) not in paths:
    paths.append(str(original))

graph = importlib.import_module(
    "cta_max.grecbase_fusion_full_head_72_max"
)
assert Path(graph.__file__).resolve() == (
    candidate / "grecbase_fusion_full_head_72_max.py"
).resolve()
print("CORRECT BATCH-2 GRAPH: PASS", flush=True)

from pipeline import pipeline as CTA
from cta_max.live_cta_pipeline_bridge import attach_max
from native_batch2.cta_worker_adapter import CTAWorkerAdapter
from native_batch2.cta_native_scheduler import CTANativeScheduler

base = Path("/workspace/artifacts/v1.168-max")

body1 = json.loads(
    (base / "cta_native_adjusted_sanity_input.json").read_text()
)
body2 = json.loads(
    (base / "test-results/cta_max_tiles_smoketest_input.json").read_text()
)

assert body1 != body2

adapter = CTAWorkerAdapter(CTA, attach_max)

observed = {"calls": 0, "responses": None}
original_batch = adapter.predict_batch

def tracked_batch(bodies):
    observed["calls"] += 1
    assert len(bodies) == 2
    responses = original_batch(bodies)
    observed["responses"] = responses
    return responses

adapter.predict_batch = tracked_batch

def reject_single(*args, **kwargs):
    raise RuntimeError("Unexpected single-request dispatch")

adapter.predict = reject_single

class InMemoryDrainer:
    def __init__(self, items):
        self.items = list(items)

    def start_draining(self):
        pass

    def retrieve_item(self):
        if not self.items:
            raise Empty()
        return self.items.pop(0)

request_queue = Queue()
response_queue = Queue()
cancel_queue = Queue()

scheduler = CTANativeScheduler(
    adapter=adapter,
    request_queue=request_queue,
    response_queue=response_queue,
    cancel_queue=cancel_queue,
    max_items_per_iteration=2,
)

ids = ["cta-batch-test-1", "cta-batch-test-2"]

contexts = [
    SimpleNamespace(request_id=ids[0], body=body1, status=None),
    SimpleNamespace(request_id=ids[1], body=body2, status=None),
]

# Test the real scheduler dispatch logic without starting
# a MAX Serve worker or modifying the live queues.
scheduler.drainer = InMemoryDrainer(contexts)

print("NATIVE SCHEDULER BATCH CAPACITY: 2", flush=True)
print("REAL MAX SCHEDULER BATCH: START", flush=True)

scheduler.run_iteration()

assert observed["calls"] == 1, (
    f"Expected one batch call, got {observed['calls']}"
)
print("ONE REAL BATCH BACKEND CALL: PASS", flush=True)

responses = observed["responses"]
assert isinstance(responses, list) and len(responses) == 2

for i, response in enumerate(responses, 1):
    prediction = response["jsonData"]["prediction"]
    assert isinstance(prediction, dict)
    print(f"CTA JSON RESPONSE {i}: PASS", flush=True)

result_map = response_queue.get_nowait()

assert isinstance(result_map, dict)
assert len(result_map) == 2

returned_ids = {str(k) for k in result_map}
assert returned_ids == set(ids), (
    f"Request ID mismatch: {returned_ids}"
)

print("NATIVE SCHEDULER REQUEST ID MAPPING: PASS", flush=True)
print("DEVELOPMENT SCHEDULER REAL MAX BATCH E2E: PASS", flush=True)
PY

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"

grep -E 'PASS|START|Error|ERROR|Traceback|STOP|DISTINCT REAL INPUT' "$LOG" | tail -35 || true
tail -12 "$LOG"

if [ "$RC" -eq 0 ] &&
   grep -q 'DEVELOPMENT SCHEDULER REAL MAX BATCH E2E: PASS' "$LOG"; then
  echo "DEVELOPMENT SCHEDULER INTEGRATION: PASS"
else
  echo "DEVELOPMENT SCHEDULER INTEGRATION: NOT VALIDATED"
fi

echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
exit "$RC"
SH
