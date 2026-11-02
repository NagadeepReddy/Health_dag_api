ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

file = Path(os.environ["ROOT"]) / "grecbase_fusion_full_head_72_max.py"
original = file.read_text()
lines = original.splitlines(keepends=True)

matches = [i for i, line in enumerate(lines)
           if "graph = Graph(" in line]
assert len(matches) == 1, "STOP: unexpected graph definition"

i = matches[0]
line = lines[i]

marker = "TensorType(DType.int64, [1, 5]"
assert line.count(marker) == 1, "STOP: NLP boundary not found"

left, right = line.split(marker, 1)

old_jet = "[1, 20], device=device) for _ in range(3)"
new_jet = "[1, 50], device=device) for _ in range(3)"

assert left.count(old_jet) == 1, "STOP: JET pattern differs"
assert right.count("[1, 50]") == 3, "STOP: sequence pattern differs"

left = left.replace(old_jet, new_jet)
right = right.replace("[1, 50]", "[1, 20]")

lines[i] = left + marker + right
updated = "".join(lines)
compile(updated, str(file), "exec")

backup = file.with_suffix(".py.before_bplan_input_order_fix")
assert not backup.exists(), "STOP: backup already exists"

backup.write_text(original)
file.write_text(updated)

print("BPLAN JET INPUTS: PASS (50)")
print("BPLAN SEQUENCE INPUTS: PASS (20)")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
