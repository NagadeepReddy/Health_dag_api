ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
file = root / "bplan_max_dev/run_real_sanity_input_adapter.py"

old = 'freq_dir = BASE / "sequence_weights"'
new = 'freq_dir = BASE.parent / "max_weights"'

assert file.is_file()
assert len(list((root / "max_weights").glob(
    "sequence_transformer.*rotary_emb.inv_freq.npy"
))) == 2, "STOP: expected two BPLAN sequence rotary weights"

source = file.read_text()
assert source.count(old) == 1, "STOP: unexpected adapter configuration"

backup = file.with_suffix(".py.before_bplan_rotary_fix")
assert not backup.exists(), "STOP: backup already exists"

updated = source.replace(old, new)
compile(updated, str(file), "exec")

backup.write_text(source)
file.write_text(updated)

print("BPLAN ROTARY WEIGHT PATH: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
