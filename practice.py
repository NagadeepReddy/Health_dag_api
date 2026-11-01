ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
file = root / "bplan_max_dev/grecbase_get_path_max.py"
weights = root / "max_weights"

for name in ("remove_tasks_dense1.weight.npy",
             "remove_tasks_dense1.bias.npy"):
    assert (weights / name).is_file(), f"Missing: {name}"

original = file.read_text()
old = 'WEIGHTS = Path(__file__).parent / "get_path_weights"'
new = 'WEIGHTS = Path(__file__).resolve().parent.parent / "max_weights"'

assert original.count(old) == 1, "STOP: Check actual WEIGHTS definition"

backup = file.with_suffix(".py.before_bplan_weight_fix")
assert not backup.exists(), "STOP: Backup already exists"

updated = original.replace(old, new)
compile(updated, str(file), "exec")

backup.write_text(original)
file.write_text(updated)

print("BPLAN MAX WEIGHT PATH: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
