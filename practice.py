cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout -k 5s 90s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY' \
  > /tmp/cta_socket_trace.log 2>&1
import runpy
from max.serve.queue.zmq_queue import ZmqPullSocket, ZmqPushSocket

original_send = ZmqPushSocket.put_nowait
original_recv = ZmqPullSocket.get_nowait

def trace_send(self, msg):
    if isinstance(msg, dict) and msg:
        print("CTA SOCKET SEND:", list(msg.keys()), flush=True)
    result = original_send(self, msg)
    if isinstance(msg, dict) and msg:
        print("CTA SOCKET SEND COMPLETE", flush=True)
    return result

def trace_recv(self):
    result = original_recv(self)
    if isinstance(result, dict) and result:
        print("CTA SOCKET RECEIVE:", list(result.keys()), flush=True)
    return result

ZmqPushSocket.put_nowait = trace_send
ZmqPullSocket.get_nowait = trace_recv

runpy.run_path(
    "/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py",
    run_name="__main__"
)
PY

rc=$?
echo "TEST EXIT: $rc"
grep -E 'CTA SOCKET|CTA NATIVE HTTP STATUS|ValidationError|Traceback|Error' \
  /tmp/cta_socket_trace.log | tail -15
