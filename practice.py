python3 - <<'PY'
from pathlib import Path

ROOT = Path("/application1")
BPLAN = ROOT / "sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev"
CTA = ROOT / "CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension"

names = (
    "native_scheduler.py",
    "native_worker_registration.py",
    "native_launcher.py",
    "spawn_worker.py",
    "native_scheduler_factory.py",
)

terms = (
    "zmqconfig", "request_queue", "response_queue",
    "deserialize", "serialize", "drainer",
    "load_scheduler", "scheduler_factory",
    "schedulerresult", "max_items_per_iteration",
    "queue_config", "queue_type"
)

for label, base in [("BPLAN", BPLAN), ("CTA", CTA)]:
    print(f"\n========== {label} QUEUE IMPLEMENTATION ==========")
    if not base.exists():
        print("DIRECTORY MISSING:", base)
        continue

    files = sorted(
        p for p in base.rglob("*.py")
        if any(p.name.endswith(n) for n in names)
    )

    for file in files:
        lines = file.read_text(errors="replace").splitlines()
        matches = [
            i for i, line in enumerate(lines)
            if any(t in line.lower() for t in terms)
        ]
        if not matches:
            continue

        print(f"\n--- {file.relative_to(base)} ---")
        shown = set()
        for i in matches[:22]:
            for j in range(max(0, i-2), min(len(lines), i+4)):
                if j not in shown:
                    print(f"{j+1:4}: {lines[j][:180]}")
                    shown.add(j)
PY
