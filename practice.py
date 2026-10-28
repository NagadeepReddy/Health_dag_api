cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout 30s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -i --rm --pull=never \
  --network=none --read-only \
  --memory=2g --pids-limit=32 \
  --tmpfs /tmp:rw,size=128m,mode=1777 \
  --tmpfs /root/.cache:rw,size=64m,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=256m,mode=1777 \
  -e HOME=/tmp -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace \
  -v "$PWD/artifacts/v1.168-max/maxserve_cta_extension:/workspace/maxserve_cta_extension:ro" \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local -B - <<'PY'
import asyncio
import multiprocessing as mp
import queue
import time
import zmq
from types import SimpleNamespace

from max.interfaces.request import RequestID
from max.interfaces.scheduler import SchedulerResult
from max.serve.queue.zmq_queue import ZmqConfig
from max.serve.scheduler.queues import EngineQueue
from maxserve_cta_extension.cta_context import CTAContext
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

class Configs:
    def __init__(self):
        output = dict[RequestID, SchedulerResult[CTASerializableOutput]]
        self.request_queue_config = ZmqConfig[CTAContext](CTAContext)
        self.response_queue_config = ZmqConfig[output](output)
        self.cancel_queue_config = ZmqConfig[list[RequestID]](list[RequestID])

    def api_worker_queues(self):
        return (
            self.request_queue_config.push(),
            self.response_queue_config.pull(),
            self.cancel_queue_config.push(),
        )

    def model_worker_queues(self):
        return (
            self.request_queue_config.pull(),
            self.response_queue_config.push(),
            self.cancel_queue_config.pull(),
        )

def model_process(config):
    request_in, response_out, cancel_in = config.model_worker_queues()

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            context = request_in.get_nowait()
            print("CROSS-PROCESS REQUEST: PASS", flush=True)

            rid = RequestID(context.request_id)
            response_out.put_nowait({
                rid: SchedulerResult.create(
                    CTASerializableOutput(
                        is_done=True,
                        result={"status": "ok"}
                    )
                )
            })

            print("CROSS-PROCESS RESPONSE SEND: PASS", flush=True)
            return

        except (queue.Empty, zmq.Again):
            time.sleep(0.05)

    raise TimeoutError("Model process did not receive request")

async def main():
    config = Configs()
    engine = EngineQueue(
        worker_monitor=SimpleNamespace(is_healthy=lambda: True),
        scheduler_zmq_configs=config,
    )

    process = mp.get_context("fork").Process(
        target=model_process,
        args=(config,)
    )

    receiver = asyncio.create_task(engine.response_worker())
    process.start()

    try:
        await asyncio.sleep(0.5)

        raw_id = "cta-cross-process-test"
        rid = RequestID(raw_id)

        with engine.open_channel(
            rid, CTAContext(raw_id, {"probe": True})
        ) as pending:
            print("HTTP REQUEST SUBMITTED: PASS", flush=True)

            result = await asyncio.wait_for(
                pending.get(), timeout=12
            )

            assert result.result.result["status"] == "ok"

            print("HTTP RESPONSE RECEIVED: PASS", flush=True)
            print("CROSS-PROCESS LIFECYCLE: PASS", flush=True)

    finally:
        receiver.cancel()
        await asyncio.gather(receiver, return_exceptions=True)

        await asyncio.to_thread(process.join, 2)
        if process.is_alive():
            process.terminate()
            await asyncio.to_thread(process.join, 2)

        print("MODEL PROCESS EXIT:", process.exitcode, flush=True)

asyncio.run(main())
PY

echo "CROSS-PROCESS TEST EXIT CODE: $?"
