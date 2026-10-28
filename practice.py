cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout 25s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -i --rm --pull=never \
  --network=none --read-only \
  --memory=1g --pids-limit=32 \
  --tmpfs /tmp:rw,size=128m,mode=1777 \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD/artifacts/v1.168-max/maxserve_cta_extension:/workspace/maxserve_cta_extension:ro" \
  -e PYTHONPATH=/workspace \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local -B - <<'PY'
import time
import queue
import zmq

from max.interfaces.request import RequestID
from max.interfaces.scheduler import SchedulerResult
from max.serve.queue.zmq_queue import ZmqConfig
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

response_type = dict[RequestID, SchedulerResult[CTASerializableOutput]]
config = ZmqConfig[response_type](response_type)

receiver = config.pull()
sender = config.push()

request_id = RequestID("cta-queue-smoke-test")
payload = {
    request_id: SchedulerResult.create(
        CTASerializableOutput(is_done=True, result={"status": "ok"})
    )
}

try:
    time.sleep(0.3)
    sender.put_nowait(payload)
    print("QUEUE SEND: PASS", flush=True)

    deadline = time.monotonic() + 5

    while time.monotonic() < deadline:
        try:
            received = receiver.get_nowait()
            print("QUEUE RECEIVE: PASS", flush=True)
            print("REQUEST ID MATCH:", request_id in received, flush=True)
            assert request_id in received
            assert received[request_id].result.result["status"] == "ok"
            print("MAX RESPONSE TRANSPORT: PASS", flush=True)
            break
        except (queue.Empty, zmq.Again):
            time.sleep(0.05)
    else:
        print("MAX RESPONSE TRANSPORT: TIMEOUT", flush=True)
finally:
    for socket in (sender, receiver):
        close = getattr(socket, "close", None)
        if callable(close):
            close()
PY

echo "QUEUE TEST EXIT CODE: $?"
