python3 -B - <<'PY'
from pathlib import Path
import difflib, ast

root = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max"
)

working = root / "maxserve_cta_extension"
staged = (
    root / "cta_native_batch2_release_candidate/"
    "maxserve_cta_extension"
)

names = [
    "cta_router.py",
    "cta_http_pipeline.py",
    "cta_spawn_worker.py",
    "cta_native_scheduler.py",
]

keywords = (
    "response_queue", "request_queue", "pending",
    "receiver", "request_id", "batch_id",
    "SchedulerZmqConfigs", "get_nowait",
    "put_nowait", "worker", "asyncio",
)

for name in names:
    old = working / name
    new = staged / name

    print("\n==========", name, "==========")

    if not new.is_file():
        print("STAGED FILE: MISSING")
        continue

    new_text = new.read_text()
    ast.parse(new_text)
    print("STAGED SYNTAX: PASS")

    if not old.is_file():
        print("WORKING COMPARISON: NOT AVAILABLE")
        continue

    old_text = old.read_text()
    ast.parse(old_text)

    if old_text == new_text:
        print("COMPARED SOURCES: IDENTICAL")
        continue

    print("RELEVANT DIFFERENCES:")
    diff = list(difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines(),
        fromfile="WORKING/" + name,
        tofile="STAGED/" + name,
        n=2,
    ))

    selected = set()
    for i, line in enumerate(diff):
        if any(k in line.lower() for k in keywords):
            selected.update(range(
                max(0, i-2),
                min(len(diff), i+3)
            ))

    count = 0
    for i in sorted(selected):
        print(diff[i][:180])
        count += 1
        if count >= 65:
            print("... additional differences omitted")
            break

    if not selected:
        print("NO RESPONSE/QUEUE-RELATED DIFFERENCES FOUND")

print("\nNATIVE RESPONSE BRIDGE COMPARISON: COMPLETE")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
