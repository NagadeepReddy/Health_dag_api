ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension
ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
file = root / "bplan_max_dev/parallel_transformer_block_2layers.py"
weights = root / "bplan_helper_weights_stage/grecbase_integration_weights"

assert file.is_file()
assert (weights / "fn_norm1_g.npy").is_file()
assert (weights / "fn_norm1_g_layer1.npy").is_file()

original = file.read_text()
assert original.count("sequence_weights") == 1, "STOP: unexpected path references"

backup = file.with_suffix(".py.before_bplan_path_fix")
assert not backup.exists(), "STOP: backup already exists"

updated = original.replace("sequence_weights", "grecbase_integration_weights")
compile(updated, str(file), "exec")

backup.write_text(original)
file.write_text(updated)

print("BPLAN TRANSFORMER WEIGHT PATH: FIXED")
print("BOTH LAYER WEIGHTS: PRESENT")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
