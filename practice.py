set -o pipefail

python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
original = p.read_text()
lines = original.splitlines(keepends=True)

start = next(
    (i for i, line in enumerate(lines)
     if "causal = np.triu(" in line),
    None
)

if start is None:
    raise SystemExit("STOP: Expected MAX causal mask not found. No changes.")

end = next(
    (i for i in range(start + 1, len(lines))
     if "attn = ops.softmax(scores)" in lines[i]),
    None
)

if end is None or end - start > 12:
    raise SystemExit("STOP: Unexpected attention layout. No changes.")

removed = "".join(lines[start:end])

if (
    "scores = scores + ops.constant(" not in removed
    or "causal.reshape(" not in removed
    or "dtype=scores.dtype" not in removed
):
    raise SystemExit("STOP: Causal block differs. No changes.")

replacement = (
    " " * (len(lines[start]) - len(lines[start].lstrip()))
    + "# Match original PyTorch: no causal mask; retain valid-length masking above.\n"
)

updated = "".join(lines[:start]) + replacement + "".join(lines[end:])
ast.parse(updated)

backup = p.with_name(p.stem + ".before_causal_alignment.bak")
if backup.exists():
    raise SystemExit("STOP: Backup already exists. No changes.")

shutil.copy2(p, backup)
p.write_text(updated)

print("MAX causal-mask alignment: APPLIED")
print("Backup:", backup)
print("Original PyTorch/DS files: UNCHANGED")
print("MAX Python syntax: PASS")
PY

rc=$?
if [ "$rc" -ne 0 ]; then
  exit "$rc"
fi

podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py \
  2>&1 | tail -50
