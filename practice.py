python - <<'PY'
from pathlib import Path
import numpy as np

base = Path("artifacts/v1.168-max/cta_max")

print("===== EXPORTED GET_PATH WEIGHTS =====")

found = 0
for p in sorted(base.rglob("*.npy")):
    if "remove_tasks" in p.name:
        print(p.name, np.load(p, mmap_mode="r").shape)
        found += 1

print("TOTAL:", found)

print("\n===== ORIGINAL LAYER DECLARATIONS =====")
p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
lines = p.read_text().splitlines()

for i, line in enumerate(lines, 1):
    if any(
        f"self.{name} =" in line
        for name in (
            "remove_tasks_dense1",
            "remove_tasks_act1",
            "remove_tasks_dense2",
        )
    ):
        print(f"{i}: {line.strip()}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
