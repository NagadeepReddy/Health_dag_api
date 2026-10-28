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
  -v "$PWD/artifacts/v1.168-max/maxserve_cta_extension:/workspace/maxserve_cta_extension:ro" \
  -e PYTHONPATH=/workspace \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local -B - <<'PY'
import time, queue, zmq

from max.interfaces.request import RequestID
from max.interfaces.scheduler import SchedulerResult
from max.serve.queue.zmq_queue import ZmqConfig
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

response_type = dict[RequestID, SchedulerResult[CTASerializableOutput]]
config = ZmqConfig[response_type](response_type)

receiver = config.pull()
sender = config.push()

rid = RequestID("cta-queue-smoke-test")
payload = {
    rid: SchedulerResult.create(
        CTASerializableOutput(
            is_done=True,
            result={"status": "ok"}
        )
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
            assert rid in received
            assert received[rid].result.result["status"] == "ok"
            print("QUEUE RECEIVE: PASS", flush=True)
            print("REQUEST ID MATCH: PASS", flush=True)
            print("MAX RESPONSE TRANSPORT: PASS", flush=True)
            break
        except (queue.Empty, zmq.Again):
            time.sleep(0.05)
    else:
        raise TimeoutError("Queue response not received")
finally:
    for socket in (sender, receiver):
        close = getattr(socket, "close", None)
        if callable(close):
            close()
PY

echo "QUEUE TEST EXIT CODE: $?"
