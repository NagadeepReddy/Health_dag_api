cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
STAGE="$DEV/native_batch2_live_stage"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate

test -s "$STAGE/cta_worker_adapter.py"
test -s "$STAGE/cta_native_scheduler.py"
test -s "$STAGE/cta_scheduler_factory.py"
test -s "$STAGE/cta_spawn_worker.py"
test -s "$STAGE/cta_worker_registration.py"
test -s "$CAND/cta_max/grecbase_fusion_full_head_72_max.py"

MEM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

test "$MEM" -ge 8388608 || {
  echo "STOP: Low available RAM"
  exit 1
}
test "$DISK" -ge 20971520 || {
  echo "STOP: Low disk"
  exit 1
}

TMPDIR="$DEV" timeout -k 10s 90s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 6g --cpus 2 --pids-limit 128 \
  --tmpfs /tmp:rw,size=256m \
  --tmpfs /root:rw,size=64m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH="$CAND:/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max:/batch2" \
  -v "$PWD:/workspace:ro" \
  -v "$STAGE:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -B - <<'PY'
import inspect
from pathlib import Path
from importlib import import_module

from maxserve_cta_extension.cta_worker_adapter import CTAWorkerAdapter
from maxserve_cta_extension.cta_native_scheduler import CTANativeScheduler
from maxserve_cta_extension.cta_scheduler_factory import create_cta_scheduler
from maxserve_cta_extension.cta_worker_registration import install_cta_scheduler_hook
from maxserve_cta_extension.cta_spawn_worker import install_cta_spawn_entry
from cta_max.run_batch2_contract import pack_two_requests

candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/grecbase_fusion_full_head_72_max.py"
)

graph = import_module("cta_max.grecbase_fusion_full_head_72_max")
assert Path(graph.__file__).resolve() == candidate.resolve()
print("CORRECT BATCH-2 GRAPH: PASS", flush=True)

assert callable(getattr(CTAWorkerAdapter, "predict_batch", None))
print("STAGED WORKER BATCH ADAPTER: PASS", flush=True)

capacity = inspect.signature(
    create_cta_scheduler
).parameters["max_items_per_iteration"].default

assert capacity == 2
print("NATIVE BATCH CAPACITY: 2 PASS", flush=True)

assert callable(CTANativeScheduler.run_iteration)
assert callable(install_cta_scheduler_hook)
assert callable(install_cta_spawn_entry)
assert callable(pack_two_requests)

print("MAX WORKER REGISTRATION IMPORT: PASS", flush=True)
print("MAX SPAWN HOOK IMPORT: PASS", flush=True)
print("STAGED NATIVE BATCH-2 PREFLIGHT: PASS", flush=True)
print("ORIGINAL DS: UNCHANGED", flush=True)
print("LIVE SERVER: NOT STARTED", flush=True)
PY
SH
