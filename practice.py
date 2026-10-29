cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path

base = Path("/application1/cta_max_native_release_candidate_20261028")
names = [
    "cta_http_pipeline.py",
    "cta_native_scheduler.py",
    "cta_queue_scheduler.py",
    "cta_spawn_worker.py",
    "cta_router.py",
]

terms = ("timeout", "wait_for", "120", "504", "cancel", "deadline")

for name in names:
    p = base / name
    if not p.is_file():
        continue

    matches = [
        (i, line.strip())
        for i, line in enumerate(p.read_text().splitlines(), 1)
        if any(t in line.lower() for t in terms)
    ]

    if matches:
        print("\nFILE:", name)
        for i, line in matches:
            print(f"{i}: {line[:200]}")

print("\nTIMEOUT SOURCE REVIEW: COMPLETE")
print("FILES MODIFIED: NONE")
print("MAX STARTED: NO")
PY
