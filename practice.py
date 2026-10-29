cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/real_cta_distinct_json_batch2.log"

test -s artifacts/v1.168-max/cta_native_adjusted_sanity_input.json
test -s artifacts/v1.168-max/test-results/cta_max_tiles_smoketest_input.json
test -s "$DEV/real_max_batch2_backend.py"
test ! -e "$LOG" || { echo "STOP: Log exists"; exit 1; }

MEM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')
test "$MEM" -ge 14680064 || { echo "STOP: Low RAM"; exit 1; }
test "$DISK" -ge 20971520 || { echo "STOP: Low disk"; exit 1; }

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
import json, hashlib, importlib, importlib.util
from pathlib import Path
import cta_max

candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)
original = Path("/workspace/artifacts/v1.168-max/cta_max")

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

p = Path("/batch2/native_batch2/cta_worker_adapter.py")
spec = importlib.util.spec_from_file_location("cta_batch_dev", p)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = Path("/workspace/artifacts/v1.168-max")
a = json.loads(
    (base / "cta_native_adjusted_sanity_input.json").read_text()
)
b = json.loads(
    (base / "test-results/cta_max_tiles_smoketest_input.json").read_text()
)

def digest(body):
    return hashlib.sha256(
        json.dumps(body, sort_keys=True).encode()
    ).hexdigest()

assert digest(a) != digest(b), "STOP: Identical JSON requests"
print("DISTINCT CTA JSON PAYLOADS: PASS", flush=True)

adapter = module.CTAWorkerAdapter(CTA, attach_max)
responses = adapter.predict_batch([a, b])

assert isinstance(responses, list) and len(responses) == 2

for i, response in enumerate(responses, 1):
    prediction = response["jsonData"]["prediction"]
    assert isinstance(prediction, dict)
    offers = prediction.get("offerList")
    print(
        f"CTA RESPONSE {i}: PASS; "
        f"offer_count={len(offers) if isinstance(offers, list) else 'N/A'}",
        flush=True
    )

print("DISTINCT CTA JSON BATCH-2 E2E: PASS", flush=True)
PY

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
grep -E 'PASS|DISTINCT REAL INPUT TENSORS|ERROR|Error|Traceback|STOP|offer_count' "$LOG" | tail -35 || true
tail -8 "$LOG"

if [ "$RC" -eq 0 ] &&
   grep -q 'DISTINCT CTA JSON BATCH-2 E2E: PASS' "$LOG" &&
   grep -Eq 'DISTINCT REAL INPUT TENSORS: [1-9][0-9]*' "$LOG"; then
  echo "DISTINCT MODEL-INPUT BATCH-2: PASS"
else
  echo "DISTINCT MODEL-INPUT BATCH-2: NOT YET VERIFIED"
fi
echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
SH
