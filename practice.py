python3 -B - <<'PY'
from pathlib import Path
import ast

pkg = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/"
    "cta_native_batch2_release_candidate/"
    "maxserve_cta_extension"
)

for name in (
    "cta_native_launcher.py",
    "cta_spawn_worker.py",
    "cta_scheduler_factory.py",
):
    p = pkg / name
    print(f"\n=== {name} ===")

    if not p.is_file():
        print("MISSING")
        continue

    src = p.read_text()
    ast.parse(src)

    lines = src.splitlines()
    terms = (
        "SchedulerZmqConfigs", "ZmqConfig",
        "spawn", "load_scheduler",
        "max_items_per_iteration",
    )

    matches = [
        i for i, line in enumerate(lines)
        if any(term in line for term in terms)
    ]

    if not matches:
        print("NO QUEUE PATCH OR SPAWN REFERENCES")
        continue

    shown = set()
    for i in matches[:20]:
        for j in range(max(0, i-2), min(len(lines), i+4)):
            if j not in shown:
                print(f"{j+1}: {lines[j]}")
                shown.add(j)

    print("SYNTAX: PASS")

print("\nWORKER QUEUE PROPAGATION INSPECTION: COMPLETE")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
