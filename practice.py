cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import shutil
import ast

src = Path("artifacts/v1.168-max/maxserve_cta_extension")
dst = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2")

names = [
    "cta_native_scheduler.py",
    "cta_scheduler_factory.py",
    "cta_worker_adapter.py",
]

for name in names:
    original = src / name
    assert original.is_file(), f"STOP: Missing {original}"

    code = original.read_text()
    ast.parse(code, filename=str(original))

    destination = dst / name
    if destination.exists():
        assert destination.read_bytes() == original.read_bytes(), (
            f"STOP: Existing development copy differs: {destination}"
        )

dst.mkdir(parents=True, exist_ok=True)

for name in names:
    original = src / name
    destination = dst / name

    if not destination.exists():
        shutil.copy2(original, destination)

    print("DEV COPY:", destination)

scheduler = (src / "cta_native_scheduler.py").read_text().splitlines()

print("\n=== NATIVE BATCHING IMPLEMENTATION POINTS ===")
for i, line in enumerate(scheduler, 1):
    if any(x in line for x in (
        "max_items_per_iteration",
        "batching not yet supported",
        "retrieve_item(",
        "adapter.predict(",
        "run_iteration("
    )):
        print(f"{i}: {line.strip()}")

print("\nDEV IMPLEMENTATION FILES: READY")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
