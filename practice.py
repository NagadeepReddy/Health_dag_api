
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import re

base = Path("/application1/sajjna8")

models = {
    "PZAAS WORKING SHARED PACKAGE":
        base / "PZAAS_MAX_CLEAN_HANDOFF_20261106",
    "CTA SHARED INTEGRATION":
        base / "max_shared_infra/isolated/cta_shared_wiring_v1",
    "BPLAN SHARED INTEGRATION":
        base / "max_shared_infra/isolated/bplan_shared_wiring_v1",
}

print("=== SHARED MAX CONFIGURATION PREPARATION ===")

for name, root in models.items():
    print(f"\n=== {name} ===")
    print("LOCATION:", root)
    if not root.is_dir():
        print("STATUS: NOT FOUND")
        continue

    print("ROOT CONTENTS:")
    for p in sorted(root.iterdir())[:30]:
        print(" DIR " if p.is_dir() else " FILE", p.name)

    print("MODEL DIRECTORY:", (root / "model").is_dir())
    print("DEPENDENCIES:",
          (root / "runtime/python_deps").is_dir())

    config = root / "config/model.env"
    print("SHARED CONFIG:", "PRESENT" if config.is_file()
          else "MISSING")

    if config.is_file():
        print("NON-SECRET CONFIGURATION:")
        for line in config.read_text().splitlines():
            if re.match(
                r"^(MODULE|INTERNAL_PORT|HOST_PORT|"
                r"MODEL_PYTHONPATH|MAX_IMAGE|MAX_MEMORY|MAX_PIDS)=",
                line
            ):
                print(" ", line)

print("\n=== ORIGINAL HANDOFF STRUCTURE ===")
for name, path in {
    "CTA": Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"),
    "BPLAN": Path("/application1/BPLAN_MAX_TEAM_HANDOFF_20261102"),
}.items():
    print(f"\n{name}:")
    for p in sorted(path.iterdir())[:20] if path.is_dir() else []:
        print(" DIR " if p.is_dir() else " FILE", p.name)

print("\nFILES MODIFIED: NONE")
print("CONTAINERS STARTED: NONE")
print("NEXT: CREATE TWO ISOLATED SHARED MODEL CONFIGURATIONS")
PY
