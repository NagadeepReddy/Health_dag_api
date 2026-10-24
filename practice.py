cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout -k 5s 90s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY' \
  > /tmp/cta_handoff_check.log 2>&1
import runpy, contextlib, asyncio
from max.serve.api_server import TokenGeneratorPipeline
from max.serve.queue.zmq_queue import ZmqPullSocket
from max.interfaces.scheduler import SchedulerResult

EngineQueue = TokenGeneratorPipeline.__init__.__globals__["EngineQueue"]
original_open = EngineQueue.open_channel
original_recv = ZmqPullSocket.get_nowait
original_put = asyncio.Queue.put
active = []

@contextlib.contextmanager
def traced_open(self, req_id, data):
    active.append(self)
    with original_open(self, req_id, data) as q:
        print("HTTP WAITING ID:", repr(req_id), flush=True)
        yield q

def traced_recv(self):
    result = original_recv(self)
    if isinstance(result, dict) and result:
        for engine in active:
            for rid in result:
                print("WORKER RESPONSE ID:", repr(rid), flush=True)
                print("HTTP PENDING IDS:", list(engine.pending_out_queues), flush=True)
                print("REQUEST ID MATCH:", rid in engine.pending_out_queues, flush=True)
    return result

async def traced_put(self, item):
    if isinstance(item, SchedulerResult):
        print("HTTP RESPONSE ENQUEUED: YES", flush=True)
    return await original_put(self, item)

EngineQueue.open_channel = traced_open
ZmqPullSocket.get_nowait = traced_recv
asyncio.Queue.put = traced_put

runpy.run_path(
    "/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py",
    run_name="__main__"
)
PY

rc=$?
echo "TEST EXIT: $rc"
grep -E 'HTTP WAITING ID|WORKER RESPONSE ID|HTTP PENDING IDS|REQUEST ID MATCH|HTTP RESPONSE ENQUEUED|CTA NATIVE HTTP STATUS|Traceback|ValidationError' \
  /tmp/cta_handoff_check.log | tail -15
