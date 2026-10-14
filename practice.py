set -o pipefail

python3 - <<'PY'
from pathlib import Path
import shutil
import ast

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")

old = "scores = ops.where(positions >= valid, negative, scores)"
new = "scores = ops.where(positions < valid, negative, scores)"

s = p.read_text()

if s.count(old) != 1:
    raise SystemExit("STOP: Expected mask expression not found exactly once.")

backup = p.with_suffix(".before_valid_mask_fix.bak")

if backup.exists():
    raise SystemExit("STOP: Backup already exists.")

updated = s.replace(old, new, 1)
ast.parse(updated)

shutil.copy2(p, backup)
p.write_text(updated)

print("MAX valid-length mask aligned with original PyTorch")
print("Backup:", backup)
print("Original DS files: UNCHANGED")
print("Python syntax: PASS")
PY

rc=$?
if [ "$rc" -ne 0 ]; then exit "$rc"; fi

podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py \
  2>&1 | tail -50
