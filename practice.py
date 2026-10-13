cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
set -e

python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py")
src = p.read_text()

old_ref = 'ref_path = BASE / "real_sanity_pytorch_output.npy"'
new_ref = 'ref_path = BASE / "real_sanity_pytorch_same_input_verified.npz"'

old_load = 'np.load(ref_path, allow_pickle=False).astype(np.float32)'
new_load = 'np.load(ref_path, allow_pickle=False)["final"].astype(np.float32)'

assert src.count(old_ref) == 1, "STOP: Unexpected reference"
assert src.count(old_load) == 1, "STOP: Unexpected reference loader"

src = src.replace(old_ref, new_ref)
src = src.replace(old_load, new_load)

lines = src.splitlines(keepends=True)

a = [i for i, x in enumerate(lines)
     if 'saved = BASE / "real_sanity_max_2048_full_runner.npy"' in x]
b = [i for i, x in enumerate(lines)
     if 'if result.shape == (1, 10819):' in x]

assert len(a) == len(b) == 1, "STOP: Unexpected save block"
a, b = a[0], b[0]
assert 5 <= b - a <= 12, "STOP: Unexpected block size"

block = "".join(lines[a:b])
assert "if not saved.exists():" in block
assert "np.save(saved, result)" in block
assert "EXISTING OUTPUT PRESERVED:" in block

indent = lines[a][:len(lines[a]) - len(lines[a].lstrip())]

replacement = [
    indent + 'saved = BASE / "real_sanity_max_2048_verified_latest.npy"\n',
    indent + 'np.save(saved, result)\n',
    indent + 'print("CURRENT MAX OUTPUT SAVED:", saved)\n',
    '\n'
]

updated = "".join(lines[:a] + replacement + lines[b:])
ast.parse(updated)

backup = p.with_name(p.name + ".before_verified_reference_fix")
assert not backup.exists(), "STOP: Backup already exists"

shutil.copy2(p, backup)
p.write_text(updated)

print("RUNNER FIX: PASS")
print("Verified PyTorch reference selected")
print("Latest MAX output will be saved")
print("Original MAX graph unchanged")
print("Python syntax: PASS")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
