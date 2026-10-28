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
import queue
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

async def main():
    cfg = Configs()
    engine = EngineQueue(
        worker_monitor=SimpleNamespace(is_healthy=lambda: True),
        scheduler_zmq_configs=cfg,
    )

    request_in, response_out, cancel_in = cfg.model_worker_queues()
    rid = RequestID("cta-lifecycle-test")

    async def worker():
        while True:
            try:
                context = request_in.get_nowait()
                print("REQUEST RECEIVED: PASS", flush=True)
                print("REQUEST ID:", repr(context.request_id), flush=True)
                response_out.put_nowait({
                    context.request_id: SchedulerResult.create(
                        CTASerializableOutput(
                            is_done=True,
                            result={"status": "ok"}
                        )
                    )
                })
                print("RESPONSE SENT: PASS", flush=True)
                return
            except (queue.Empty, zmq.Again):
                await asyncio.sleep(0.05)

    receiver_task = asyncio.create_task(engine.response_worker())
    worker_task = asyncio.create_task(worker())

    try:
        await asyncio.sleep(0.5)
        print("RECEIVER STARTED:", not receiver_task.done(), flush=True)

        with engine.open_channel(rid, CTAContext(rid, {"probe": True})) as pending:
            print("REQUEST SUBMITTED: PASS", flush=True)
            try:
                result = await asyncio.wait_for(pending.get(), timeout=8)
                assert result.result.result["status"] == "ok"
                print("HTTP PENDING RESPONSE: PASS", flush=True)
            except asyncio.TimeoutError:
                print("HTTP PENDING RESPONSE: TIMEOUT", flush=True)
                print("WORKER TASK DONE:", worker_task.done(), flush=True)
                if worker_task.done():
                    print("WORKER ERROR:", repr(worker_task.exception()), flush=True)
                print("RECEIVER TASK DONE:", receiver_task.done(), flush=True)
                if receiver_task.done():
                    print("RECEIVER ERROR:", repr(receiver_task.exception()), flush=True)
                raise

        print("NATIVE QUEUE LIFECYCLE: PASS", flush=True)
    finally:
        for task in (receiver_task, worker_task):
            task.cancel()
        await asyncio.gather(receiver_task, worker_task, return_exceptions=True)

asyncio.run(main())
PY

echo "LIFECYCLE EXIT CODE: $?"
