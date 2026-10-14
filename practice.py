(
set -euo pipefail

f="artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py"
backup="$(mktemp)"
cp "$f" "$backup"
trap 'cp "$backup" "$f"; rm -f "$backup"' EXIT

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py")
s = p.read_text()

old = ") * -1.0e9"
assert s.count(old) == 1, "STOP: Mask expression differs; no change made"

p.write_text(s.replace(old, ") * 0.0", 1))
print("TEMPORARY CAUSAL-MASK TEST: READY")
PY

podman run --rm -i --pull=never \
  -v "$PWD:/workspace:ro" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py \
  2>&1 | grep -E 'sequence (PASS|FAIL)|CURRENT BRANCH PARITY|VERIFIED FINAL MAX_DIFF|VERIFIED FINAL MATCH|Traceback|Error|AssertionError'

echo "MAX source automatically restored"
)
