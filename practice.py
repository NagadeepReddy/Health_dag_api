ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
file = root / "bplan_max_dev/sequence_postprocess_max.py"
weights = root / "bplan_helper_weights_stage/grecbase_integration_weights"

assert file.is_file()
for name in ("out_norm1_g.npy", "out_norm2_g.npy"):
    assert (weights / name).is_file(), f"STOP: missing {name}"

original = file.read_text()
assert original.count("sequence_weights") == 1, "STOP: unexpected references"

updated = original.replace("sequence_weights", "grecbase_integration_weights")
compile(updated, str(file), "exec")

backup = file.with_suffix(".py.before_bplan_path_fix")
assert not backup.exists(), "STOP: backup already exists"

backup.write_text(original)
file.write_text(updated)

print("BPLAN SEQUENCE POSTPROCESS PATH: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
