python3 - <<'PY'
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

files = [
    base / "native_batch2_cached_overlay/cta_native_scheduler.py",
    base / "native_batch2_cached_overlay/cta_worker_adapter.py",
    Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/maxserve_cta_extension/cta_native_scheduler.py"),
]

terms = (
    "predict_batch",
    "response_queue",
    "SchedulerResult",
    "put_nowait",
    "send_output",
    "responses[",
)

for path in files:
    if not path.is_file():
        continue

    print(f"\n=== {path} ===")
    lines = path.read_text().splitlines()
    selected = set()

    for i, line in enumerate(lines):
        if any(term in line for term in terms):
            selected.update(range(max(0, i-5), min(len(lines), i+9)))

    for i in sorted(selected):
        print(f"{i+1}: {lines[i]}")

print("\nRESULT DELIVERY CODE: EXTRACTED")
print("ORIGINAL DS: UNCHANGED")
print("BOTH LIVE SERVERS: UNTOUCHED")
PY
