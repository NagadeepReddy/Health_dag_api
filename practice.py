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
from maxserve_cta_extension import cta_http_pipeline
from max.serve.scheduler.queues import SchedulerZmqConfigs
from max.interfaces.task import PipelineTask
from max.interfaces.scheduler import SchedulerResult
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

cfg = SchedulerZmqConfigs(PipelineTask.TEXT_GENERATION)
rx = cfg.response_queue_config.pull()
tx = cfg.response_queue_config.push()

try:
    time.sleep(0.3)
    tx.put_nowait({
        "cta-test": SchedulerResult.create(
            CTASerializableOutput(
                is_done=True, result={"status": "ok"}
            )
        )
    })
    for _ in range(30):
        try:
            result = rx.get_nowait()
            assert result["cta-test"].result.result == {"status": "ok"}
            print("CTA ZMQ RESPONSE TRANSPORT: PASS")
            break
        except queue.Empty:
            time.sleep(0.1)
    else:
        print("CTA ZMQ RESPONSE TRANSPORT: FAIL - NO MESSAGE")
except Exception as e:
    print("CTA ZMQ RESPONSE TRANSPORT: FAIL", type(e).__name__, str(e))
finally:
    tx.close()
    rx.close()
PY
