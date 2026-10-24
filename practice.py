cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout -k 5s 75s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY' \
  > /tmp/cta_dispatch_trace.log 2>&1
import runpy
from contextlib import contextmanager
from max.serve.api_server import TokenGeneratorPipeline
from max.serve.queue.zmq_queue import ZmqPullSocket

EngineQueue = TokenGeneratorPipeline.__init__.__globals__["EngineQueue"]
original_open = EngineQueue.open_channel
original_recv = ZmqPullSocket.get_nowait
engines = []

@contextmanager
def traced_open(self, rid, data):
    engines.append(self)
    with original_open(self, rid, data) as q:
        print("HTTP PENDING:", repr(rid), flush=True)
        yield q

def traced_recv(self):
    result = original_recv(self)
    if isinstance(result, dict) and result:
        for engine in engines:
            for rid in result:
                pending = engine.pending_out_queues
                print("RESPONSE RECEIVED:", repr(rid), flush=True)
                print("PENDING KEYS:", list(pending), flush=True)
                print("DISPATCH MATCH:", rid in pending, flush=True)
    return result

EngineQueue.open_channel = traced_open
ZmqPullSocket.get_nowait = traced_recv

runpy.run_path(
    "/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py",
    run_name="__main__"
)
PY

rc=$?
echo "TEST EXIT: $rc"
grep -E 'HTTP PENDING:|RESPONSE RECEIVED:|PENDING KEYS:|DISPATCH MATCH:|CTA NATIVE HTTP STATUS|Traceback|ValidationError' \
  /tmp/cta_dispatch_trace.log | tail -12
