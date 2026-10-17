
python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_scheduler.py")

if p.exists():
    raise SystemExit("STOP: CTA scheduler already exists; not overwriting")

code = '''
from queue import Queue, Empty
from threading import Lock

from max.interfaces.scheduler import Scheduler, SchedulerProgress


class CTAScheduler(Scheduler):
    """CTA request scheduler using the existing real MAX adapter."""

    def __init__(self, adapter, max_items_per_iteration=1):
        if max_items_per_iteration < 1:
            raise ValueError("Iteration limit must be positive")
        self.adapter = adapter
        self.max_items_per_iteration = max_items_per_iteration
        self.pending = Queue()
        self.completed = {}
        self.lock = Lock()

    def submit(self, request_id, body):
        if not isinstance(body, dict):
            raise TypeError("CTA request must be a JSON object")
        self.pending.put((request_id, body))

    def run_iteration(self):
        processed = 0

        while processed < self.max_items_per_iteration:
            try:
                request_id, body = self.pending.get_nowait()
            except Empty:
                break

            try:
                result = self.adapter.predict(body)
                outcome = (True, result)
            except Exception as exc:
                outcome = (False, exc)

            with self.lock:
                self.completed[request_id] = outcome

            self.pending.task_done()
            processed += 1

        return (
            SchedulerProgress.MADE_PROGRESS
            if processed
            else SchedulerProgress.NO_PROGRESS
        )

    def take_result(self, request_id):
        with self.lock:
            success, value = self.completed.pop(request_id)
        if not success:
            raise value
        return value
'''

ast.parse(code)
p.write_text(code)
print("CTA SCHEDULER CREATED — SYNTAX PASS")
print("Existing DS and MAX inference files untouched")
PY
