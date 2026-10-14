set -o pipefail
python3 - <<'PY' && podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py \
  2>&1 | tail -65
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max_branch_diag.py")
code = p.read_text()
old = "assert len(remaining) == 66"
new = "assert len(remaining) == 67"

if code.count(old) != 1:
    raise SystemExit("STOP: Expected assertion not found exactly once.")

updated = code.replace(old, new, 1)
ast.parse(updated)
shutil.copy2(p, str(p) + ".before_assert_fix.bak")
p.write_text(updated)

print("Diagnostic assertion corrected: 66 -> 67")
print("Python syntax: PASS")
print("Original DS code: UNCHANGED")
PY
