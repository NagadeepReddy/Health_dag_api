cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
timeout 25s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -i --rm --pull=never \
  --network=none --read-only \
  --memory=256m --pids-limit=32 \
  --tmpfs /tmp:rw,size=32m,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=64m \
  -v "$PWD":/workspace:ro \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  -e PYTHONDONTWRITEBYTECODE=1 \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local -B - <<'PY'
import time
from queue import Empty
from max.serve.queue.zmq_queue import ZmqConfig
from max.interfaces.request import RequestID
from max.interfaces.scheduler import SchedulerResult
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

response_type = dict[RequestID, SchedulerResult[CTASerializableOutput]]
config = ZmqConfig[response_type](response_type)

sender = config.push()
receiver = config.pull()

try:
    time.sleep(0.2)
    sender.put_nowait({
        RequestID("cta-zmq-test"): SchedulerResult.create(
            CTASerializableOutput(is_done=True, result={"status": "ok"})
        )
    })

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            received = receiver.get_nowait()
            result = next(iter(received.values())).result
            assert result.result == {"status": "ok"}
            print("ZMQ RESPONSE DELIVERY: PASS")
            break
        except Empty:
            time.sleep(0.1)
    else:
        print("ZMQ RESPONSE DELIVERY: FAIL - no response received")
finally:
    sender.close()
    receiver.close()

print("MAX STARTUP: NOT PERFORMED")
print("DS CODE: UNCHANGED")
PY
