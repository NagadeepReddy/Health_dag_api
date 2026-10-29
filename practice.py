cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
INPUT=artifacts/v1.168-max/cta_native_adjusted_sanity_input.json
LOG="$DEV/real_cta_json_batch2_import_fixed.log"

test -s "$DEV/native_batch2/cta_worker_adapter.py"
test -s "$DEV/real_max_batch2_backend.py"
test -s "$INPUT"
test ! -e "$LOG" || { echo "STOP: Log already exists"; exit 1; }

test -s "$CAND/cta_max/run_batch2_contract.py" || {
  echo "STOP: Batch contract not found at expected location"
  find "$DEV" "$CAND" -name run_batch2_contract.py -print
  exit 1
}

AVAILABLE=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
test "$AVAILABLE" -ge 14680064 || {
  echo "STOP: Insufficient available RAM for safe MAX startup"
  exit 1
}

echo "=== REAL CTA JSON BATCH-2 INTEGRATION ==="

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
  -e CTA_CANDIDATE="$CAND" \
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
import os
import json
import importlib.util
from pathlib import Path

from pipeline import pipeline as CTA
from cta_max.live_cta_pipeline_bridge import attach_max
import cta_max

# Extend the existing CTA package without replacing the working bridge.
contract_dir = Path(os.environ["CTA_CANDIDATE"]) / "cta_max"
assert (contract_dir / "run_batch2_contract.py").is_file()

if str(contract_dir) not in cta_max._path_:
    cta_max._path_.append(str(contract_dir))

from cta_max.run_batch2_contract import pack_two_requests
assert callable(pack_two_requests)
print("BATCH-2 CONTRACT IMPORT: PASS", flush=True)

adapter_file = Path("/batch2/native_batch2/cta_worker_adapter.py")
spec = importlib.util.spec_from_file_location(
    "cta_batch_adapter_dev", adapter_file
)
assert spec is not None and spec.loader is not None

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert hasattr(module.CTAWorkerAdapter, "predict_batch")

input_file = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)

first = json.loads(input_file.read_text())
second = json.loads(input_file.read_text())

adapter = module.CTAWorkerAdapter(CTA, attach_max)

print("TWO REAL CTA JSON REQUESTS: START", flush=True)
responses = adapter.predict_batch([first, second])

assert isinstance(responses, list)
assert len(responses) == 2
assert all(isinstance(r, dict) for r in responses)
assert all(isinstance(r.get("jsonData"), dict) for r in responses)

print("TWO CTA JSON RESPONSE CONTRACTS: PASS", flush=True)
print("RESPONSE KEYS:", [sorted(r) for r in responses], flush=True)
print("REAL CTA JSON BATCH-2 ADAPTER: PASS", flush=True)
PY

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
tail -65 "$LOG"

if [ "$RC" -eq 0 ] &&
   grep -q 'REAL CTA JSON BATCH-2 ADAPTER: PASS' "$LOG"; then
  echo "DEVELOPMENT JSON BATCH E2E: PASS"
else
  echo "DEVELOPMENT JSON BATCH E2E: NOT VALIDATED"
fi

echo "ORIGINAL DS CODE: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
exit "$RC"
SH
