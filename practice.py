ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
file = root / "bplan_max_dev/parallel_transformer_block_2layers.py"
stage = root / "bplan_helper_weights_stage/grecbase_integration_weights"

assert file.is_file()
assert stage.is_dir()
for name in ("fn_norm1_g.npy", "fn_norm1_g_layer1.npy",
             "fn_norm2_g.npy", "fn_norm2_g_layer1.npy"):
    assert (stage / name).is_file(), f"STOP: missing {name}"

original = file.read_text()
old = "/sequence_weights/"
new = "/grecbase_integration_weights/"
count = original.count(old)

assert count > 0, "STOP: expected directory references not found"

updated = original.replace(old, new)
compile(updated, str(file), "exec")

backup = file.with_suffix(".py.before_bplan_path_fix")
assert not backup.exists(), "STOP: backup already exists"

backup.write_text(original)
file.write_text(updated)

print("BPLAN TRANSFORMER PATH FIX: PASS")
print("REFERENCES UPDATED:", count)
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
