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
  -e HOME=/tmp -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/workspace \
  -v "$PWD/artifacts/v1.168-max/maxserve_cta_extension:/workspace/maxserve_cta_extension:ro" \
  --entrypoint /opt/venv/bin/python3 \
  localhost/cta-max-faiss:local -B - <<'PY'
import asyncio, queue, zmq
from types import SimpleNamespace

from max.interfaces.request import RequestID
from max.interfaces.scheduler import SchedulerResult
from max.serve.queue.zmq_queue import ZmqConfig
from max.serve.scheduler.queues import EngineQueue
from maxserve_cta_extension.cta_context import CTAContext
from maxserve_cta_extension.cta_native_scheduler import CTASerializableOutput

class Configs:
    def __init__(self):
        response_type = dict[RequestID, SchedulerResult[CTASerializableOutput]]
        self.request_queue_config = ZmqConfig[CTAContext](CTAContext)
        self.response_queue_config = ZmqConfig[response_type](response_type)
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
    rid = RequestID("cta-http-delivery-smoke")

    async def fake_worker():
        for _ in range(200):
            try:
                context = request_in.get_nowait()
                print("NATIVE REQUEST RECEIVED: PASS", flush=True)
                response_out.put_nowait({
                    context.request_id: SchedulerResult.create(
                        CTASerializableOutput(
                            is_done=True,
                            result={"status": "ok"},
                        )
                    )
                })
                print("NATIVE RESPONSE SENT: PASS", flush=True)
                return
            except (queue.Empty, zmq.Again):
                await asyncio.sleep(0.03)
        raise TimeoutError("Request never reached model-side queue")

    receiver = asyncio.create_task(engine.response_worker())
    worker = asyncio.create_task(fake_worker())

    try:
        with engine.open_channel(rid, CTAContext(rid, {"probe": True})) as pending:
            result = await asyncio.wait_for(pending.get(), timeout=8)

        await worker
        assert result.result.result["status"] == "ok"
        print("HTTP PENDING QUEUE DELIVERY: PASS", flush=True)
        print("MAX RESPONSE LIFECYCLE: PASS", flush=True)
    finally:
        receiver.cancel()
        worker.cancel()
        await asyncio.gather(receiver, worker, return_exceptions=True)
        for sock in (request_in, response_out, cancel_in):
            close = getattr(sock, "close", None)
            if callable(close):
                close()

asyncio.run(main())
PY

echo "RESPONSE LIFECYCLE EXIT CODE: $?"
