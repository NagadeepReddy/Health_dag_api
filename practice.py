cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
from textwrap import dedent, indent
from types import SimpleNamespace
import ast

p = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2/cta_native_scheduler.py")
assert p.is_file(), f"STOP: Missing {p}"

source = p.read_text()
assert "CTA_NATIVE_BATCH_DISPATCH_V1" not in source, "STOP: Already patched"

tree = ast.parse(source)
cls = next(
    n for n in tree.body
    if isinstance(n, ast.ClassDef) and n.name == "CTANativeScheduler"
)
old = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef) and n.name == "run_iteration"
)

method = indent(dedent("""
def run_iteration(self):
    # CTA_NATIVE_BATCH_DISPATCH_V1
    self.drainer.start_draining()

    while True:
        try:
            self.cancelled_ids.update(self.cancel_queue.get_nowait())
        except Empty:
            break

    contexts = []
    limit = self.max_items_per_iteration

    while len(contexts) < limit:
        try:
            item = self.drainer.retrieve_item()
        except Empty:
            break

        if isinstance(item, dict) and "body" not in item:
            incoming = list(item.values())
        else:
            incoming = [item]

        if len(contexts) + len(incoming) > limit:
            raise RuntimeError("CTA batch exceeds configured capacity")

        for context in incoming:
            if isinstance(context, dict):
                from .cta_context import CTAContext
                context = CTAContext(
                    context["wire_request_id"], context["body"]
                )
            contexts.append(context)

    responses = {}
    active = []

    for context in contexts:
        rid = context.request_id
        if rid in self.cancelled_ids:
            context.status = GenerationStatus.CANCELLED
            responses[RequestID(rid)] = SchedulerResult.cancelled()
            self.cancelled_ids.discard(rid)
        else:
            active.append(context)

    if active:
        try:
            if len(active) == 1:
                results = [self.adapter.predict(active[0].body)]
            else:
                batch_fn = getattr(self.adapter, "predict_batch", None)
                if not callable(batch_fn):
                    raise RuntimeError(
                        "REAL MAX predict_batch backend not connected"
                    )

                results = batch_fn([c.body for c in active])

                if not isinstance(results, (list, tuple)):
                    raise TypeError("Batch backend must return a result list")
                if len(results) != len(active):
                    raise RuntimeError("Batch response count mismatch")

        except Exception as exc:
            results = [
                {"error": type(exc).__name__, "message": str(exc)}
                for _ in active
            ]

        for context, result in zip(active, results):
            context.status = GenerationStatus.END_OF_SEQUENCE
            responses[RequestID(context.request_id)] = SchedulerResult.create(
                CTASerializableOutput(is_done=True, result=result)
            )

    if responses:
        self.response_queue.put_nowait(responses)

    return (
        SchedulerProgress.MADE_PROGRESS
        if contexts else SchedulerProgress.NO_PROGRESS
    )
""").strip("\n"), "    ") + "\n"

lines = source.splitlines(keepends=True)
updated = "".join(lines[:old.lineno - 1]) + method + "".join(lines[old.end_lineno:])
ast.parse(updated)

# Test actual generated method without starting MAX.
class Empty(Exception):
    pass

class Drainer:
    def __init__(self, items):
        self.items = list(items)
    def start_draining(self):
        pass
    def retrieve_item(self):
        if not self.items:
            raise Empty()
        return self.items.pop(0)

class Queue:
    def __init__(self):
        self.items = []
    def get_nowait(self):
        raise Empty()
    def put_nowait(self, item):
        self.items.append(item)

class Adapter:
    def __init__(self):
        self.batch_calls = 0
        self.single_calls = 0
    def predict(self, body):
        self.single_calls += 1
        return {"id": body["id"]}
    def predict_batch(self, bodies):
        self.batch_calls += 1
        return [{"id": body["id"]} for body in bodies]

class Result:
    @staticmethod
    def create(x):
        return x
    @staticmethod
    def cancelled():
        return "cancelled"

scope = {
    "Empty": Empty,
    "RequestID": lambda value: value,
    "SchedulerResult": Result,
    "CTASerializableOutput": lambda **kwargs: kwargs,
    "GenerationStatus": SimpleNamespace(
        CANCELLED="cancelled", END_OF_SEQUENCE="completed"
    ),
    "SchedulerProgress": SimpleNamespace(
        MADE_PROGRESS="progress", NO_PROGRESS="none"
    ),
}
exec(dedent(method), scope)

adapter = Adapter()
queue = Queue()
contexts = [
    SimpleNamespace(request_id=f"real-{i}", body={"id": i}, status=None)
    for i in (1, 2)
]
worker = SimpleNamespace(
    drainer=Drainer(contexts),
    cancel_queue=Queue(),
    response_queue=queue,
    cancelled_ids=set(),
    max_items_per_iteration=2,
    adapter=adapter,
)

scope["run_iteration"](worker)

assert adapter.batch_calls == 1
assert adapter.single_calls == 0
assert len(queue.items) == 1
assert set(queue.items[0]) == {"real-1", "real-2"}
assert queue.items[0]["real-1"]["result"]["id"] == 1
assert queue.items[0]["real-2"]["result"]["id"] == 2

backup = p.with_suffix(".py.before_batch_dispatch.bak")
assert not backup.exists(), f"STOP: Backup already exists: {backup}"

backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("DEV NATIVE BATCH DISPATCH: INSTALLED")
print("TWO REQUEST IDS: PASS")
print("ONE BATCH BACKEND CALL: PASS (MOCK)")
print("RESPONSE MAPPING: PASS")
print("PYTHON SYNTAX: PASS")
print("BACKUP: CREATED")
print("REAL MAX BATCH BACKEND: NOT YET CONNECTED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
