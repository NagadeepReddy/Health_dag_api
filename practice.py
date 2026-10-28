cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout 35s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -i --rm --pull=never \
  --network=none --read-only \
  --memory=2g --pids-limit=32 \
  --tmpfs /tmp:rw,size=128m,mode=1777 \
  --tmpfs /root/.cache:rw,size=64m,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=256m,mode=1777 \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace \
  -v "$PWD/artifacts/v1.168-max/maxserve_cta_extension:/workspace/maxserve_cta_extension:ro" \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local -B - <<'PY'
from queue import Queue, Empty
from maxserve_cta_extension.cta_context import CTAContext
from maxserve_cta_extension.cta_native_scheduler import CTANativeScheduler

class FakeAdapter:
    def __init__(self):
        self.calls = 0

    def predict(self, body):
        self.calls += 1
        return {"request": body["number"], "status": "ok"}

class FakeDrainer:
    def __init__(self, contexts):
        self.items = list(contexts)

    def retrieve_item(self):
        if not self.items:
            raise Empty()
        return self.items.pop(0)

adapter = FakeAdapter()
responses = Queue()

scheduler = CTANativeScheduler(
    adapter=adapter,
    request_queue=Queue(),
    response_queue=responses,
    cancel_queue=Queue(),
    max_items_per_iteration=2,
)

scheduler.drainer = FakeDrainer([
    CTAContext("cta-batch-1", {"number": 1}),
    CTAContext("cta-batch-2", {"number": 2}),
])

scheduler.run_iteration()

assert adapter.calls == 2, f"Expected 2 requests, got {adapter.calls}"
assert not responses.empty(), "No scheduler response"

batch = responses.get_nowait()

assert len(batch) == 2, f"Expected 2 responses, got {len(batch)}"

print("SCHEDULER REQUEST COUNT: 2")
print("SCHEDULER RESPONSE COUNT:", len(batch))
print("TWO-REQUEST SCHEDULING: PASS")
print("REAL MODEL BATCHING: NOT YET TESTED")
print("DS CODE: UNCHANGED")
PY

echo "BATCHING TEST EXIT CODE: $?"
