cd /application1/sajjna8/rt-pzaas-cta-offers-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  -v "$PWD:/workspace:Z" \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import time
import queue
from max.interfaces.request import RequestID
from max.interfaces.scheduler import SchedulerResult
from max.serve.scheduler.queues import ZmqConfig
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

contract = dict[RequestID, SchedulerResult[CTASerializableOutput]]
config = ZmqConfig[contract](contract)
rx = config.pull()
tx = config.push()

try:
    rid = RequestID("cta-test")
    time.sleep(0.3)
    tx.put_nowait({
        rid: SchedulerResult.create(
            CTASerializableOutput(
                is_done=True, result={"status": "ok"}
            )
        )
    })
    for _ in range(30):
        try:
            response = rx.get_nowait()
            assert response[rid].result.result == {"status": "ok"}
            print("CTA TYPED ZMQ TRANSPORT: PASS")
            break
        except queue.Empty:
            time.sleep(0.1)
    else:
        print("CTA TYPED ZMQ TRANSPORT: FAIL - NO RESPONSE")
except Exception as e:
    print("CTA TYPED ZMQ TRANSPORT: FAIL", type(e).__name__, str(e))
finally:
    tx.close()
    rx.close()
PY
