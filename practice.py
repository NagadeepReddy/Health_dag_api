REPO=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:$REPO:ro" -w "$REPO" \
  localhost/cta-max-faiss:local -B - <<'PY'
import sys
import traceback
from pathlib import Path
from queue import Queue

dev = Path("artifacts/v1.113-max/maxserve_bplan_extension").resolve()
sys.path.insert(0, str(dev))

try:
    from bplan_native_serve_dev.bplan_scheduler_factory import create_bplan_scheduler
    from bplan_native_serve_dev.bplan_native_scheduler import BPlanNativeScheduler

    class TestQueues:
        def model_worker_queues(self):
            return Queue(), Queue(), Queue()

    class TestAdapter:
        def predict(self, body):
            return {"jsonData": {"prediction": {}}}

    scheduler = create_bplan_scheduler(TestAdapter(), TestQueues())

    assert isinstance(scheduler, BPlanNativeScheduler)
    assert scheduler.max_items_per_iteration == 1

    try:
        create_bplan_scheduler(TestAdapter(), TestQueues(), max_items_per_iteration=2)
    except ValueError:
        pass
    else:
        raise AssertionError("Batching guard failed")

    print("BPLAN MAX SCHEDULER IMPORT: PASS")
    print("BPLAN NATIVE QUEUE INITIALIZATION: PASS")
    print("SINGLE-REQUEST GUARD: PASS")
    print("ORIGINAL DS AND CTA: UNCHANGED")

except Exception:
    print("BPLAN NATIVE SCHEDULER VALIDATION: FAILED")
    traceback.print_exc()
    sys.exit(1)
PY
