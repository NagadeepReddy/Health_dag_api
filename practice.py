cd /application1/sajjna8/rt-pzaas-cta-offers-v1

timeout -k 5s 75s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY' \
  > /tmp/cta_receiver_trace.log 2>&1
import runpy
from max.interfaces.queue import MAXPullQueue

original = MAXPullQueue.get_nowait

def traced_receive(self):
    result = original(self)
    if isinstance(result, dict):
        print("CTA ZMQ ACTUAL RECEIVE:", list(result.keys()), flush=True)
    return result

MAXPullQueue.get_nowait = traced_receive

runpy.run_path(
    "/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py",
    run_name="__main__"
)
PY

echo "=== RECEIVER RESULT ==="
grep -E 'CTA ZMQ ACTUAL RECEIVE|CTA WORKER RESPONSE IDS: \[.|CTA NATIVE HTTP STATUS|ValidationError|Traceback|Error' \
  /tmp/cta_receiver_trace.log | tail -15
echo "EXIT CODE: $?"
