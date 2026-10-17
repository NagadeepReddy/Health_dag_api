
python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py")

code = '''
from queue import Empty

from max.interfaces.context import GenerationStatus
from max.interfaces.queue import BackgroundQueueDrainer
from max.interfaces.scheduler import Scheduler, SchedulerResult
from max.serve.scheduler.base import SchedulerProgress


class CTANativeScheduler(Scheduler):
    """Execute real CTA requests through MAX Serve native queues."""

    def __init__(
        self,
        adapter,
        request_queue,
        response_queue,
        cancel_queue,
        max_items_per_iteration=1,
    ):
        if max_items_per_iteration < 1:
            raise ValueError("Iteration limit must be positive")

        self.adapter = adapter
        self.response_queue = response_queue
        self.cancel_queue = cancel_queue
        self.max_items_per_iteration = max_items_per_iteration
        self.drainer = BackgroundQueueDrainer(
            request_queue,
            max_items_per_drain=max_items_per_iteration * 2,
        )
        self.cancelled_ids = set()

    def run_iteration(self):
        processed = 0
        self.drainer.start_draining()

        while True:
            try:
                self.cancelled_ids.update(self.cancel_queue.get_nowait())
            except Empty:
                break

        responses = {}

        while processed < self.max_items_per_iteration:
            try:
                context = self.drainer.retrieve_item()
            except Empty:
                break

            request_id = context.request_id

            if request_id in self.cancelled_ids:
                context.status = GenerationStatus.CANCELLED
                responses[request_id] = SchedulerResult.cancelled()
                self.cancelled_ids.discard(request_id)
            else:
                try:
                    result = self.adapter.predict(context.body)
                except Exception as exc:
                    result = {
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }

                context.status = GenerationStatus.END_OF_SEQUENCE
                responses[request_id] = SchedulerResult.create(result)

            processed += 1

        if responses:
            self.response_queue.put_nowait(responses)

        return (
            SchedulerProgress.MADE_PROGRESS
            if processed
            else SchedulerProgress.NO_PROGRESS
        )
'''

ast.parse(code)
with p.open("x") as f:
    f.write(code)

print("CTA NATIVE QUEUE SCHEDULER CREATED — SYNTAX PASS")
print("Existing CTA scheduler, MAX inference and DS files untouched")
PY
