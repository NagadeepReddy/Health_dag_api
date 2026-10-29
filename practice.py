cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path

candidate = Path("/application1/cta_max_native_release_candidate_20261028")
base = Path("/application1/cta_max_true_batch_dev_20261028")

files = [
    candidate / "cta_router.py",
    candidate / "cta_native_scheduler.py",
    candidate / "cta_queue_scheduler.py",
    candidate / "cta_http_pipeline.py",
    base / "native_concurrent2_static.py",
    base / "cta_native_benchmark_helper.py",
]

terms = (
    "response_queue", "receiver_queue", "response worker",
    "request_id", "requestid", "pending", "cancelled",
    "timeout", "wait_for", "504", "benchmark_post",
    "threadpoolexecutor", "schedulerresult"
)

for path in files:
    if not path.is_file():
        continue
    lines = path.read_text().splitlines()
    matched = [
        i for i, line in enumerate(lines)
        if any(term in line.lower() for term in terms)
    ]
    if not matched:
        continue

    print(f"\n=== {path.name} ===")
    selected = set()
    for i in matched:
        selected.update(range(max(0, i-2), min(len(lines), i+4)))

    for i in sorted(selected):
        print(f"{i+1}: {lines[i][:180]}")

print("\nSOURCE REVIEW COMPLETE — NO CHANGES")
print("MAX NOT STARTED")
PY
