python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")

names = [
    "bplan_native_scheduler.py",
    "bplan_http_pipeline.py",
    "bplan_native_worker_registration.py",
    "bplan_context.py",
    "bplan_router.py",
]

terms = (
    "response_queue", "queue_response", "SchedulerResult",
    "RequestID", "request_id", "wire_request_id",
    "ZmqPullSocket", "receive_response", "BPlanSerializableOutput",
    "is_done", "asyncio.timeout"
)

for name in names:
    paths = list(root.rglob(name))
    print(f"\n=== {name} ===")
    if not paths:
        print("NOT FOUND")
        continue
    p = paths[0]
    lines = p.read_text().splitlines()
    hits = [i for i, line in enumerate(lines)
            if any(term in line for term in terms)]
    show = set()
    for i in hits:
        show.update(range(max(0, i - 4), min(len(lines), i + 7)))
    for i in sorted(show):
        print(f"{i+1}: {lines[i]}")
PY
