cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
BACKEND="$DEV/real_max_batch2_backend.py"
LOG="$DEV/real_max_batch2_after_cache_fix.log"

test -s "$BACKEND"
test -d "$CAND"
test -s artifacts/v1.168-max/cta_max/real_sanity_model_in.pt
test ! -e "$LOG" || {
  echo "STOP: Preserve existing log: $LOG"
  exit 1
}

python3 -S -B - <<'PY'
from pathlib import Path
import ast
import io
import tokenize

p = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py")
source = p.read_text()

tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
matches = [
    t for t in tokens
    if t.type == tokenize.NAME and t.string == "infer_max_live"
]

assert matches, "STOP: Old identifier not present; inspect current backend"
assert "def infer_max_batch(model_in, second_model_in):" in source

updated_tokens = [
    tokenize.TokenInfo(
        t.type,
        "infer_max_batch" if t.type == tokenize.NAME and t.string == "infer_max_live" else t.string,
        t.start,
        t.end,
        t.line
    )
    for t in tokens
]

updated = tokenize.untokenize(updated_tokens)
tree = ast.parse(updated)

assert any(
    isinstance(n, ast.FunctionDef) and n.name == "infer_max_batch"
    for n in tree.body
)
assert not any(
    isinstance(n, ast.Name) and n.id == "infer_max_live"
    for n in ast.walk(tree)
)

backup = p.with_suffix(".py.before_cache_fix.bak")
assert not backup.exists(), "STOP: Backup already exists"
backup.write_bytes(p.read_bytes())
p.write_text(updated)

print("OLD MAX FUNCTION REFERENCES FIXED:", len(matches))
print("MAX SESSION CACHE: USES infer_max_batch")
print("PYTHON SYNTAX: PASS")
print("BACKUP: CREATED")
PY

echo "=== REAL MAX BATCH-2 EXECUTION ==="

set +e
timeout -k 15s 420s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 12g --cpus 4 --pids-limit 256 \
  --tmpfs /tmp:rw,size=512m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONUNBUFFERED=1 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH="/batch2:/workspace/artifacts/v1.168-max:$CAND" \
  -v "$PWD:/workspace:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -B - > "$LOG" 2>&1 <<'PY'
import numpy as np
import torch
from real_max_batch2_backend import infer_max_batch

source = "/workspace/artifacts/v1.168-max/cta_max/real_sanity_model_in.pt"

model_in = torch.load(
    source, map_location="cpu", weights_only=True
)

assert isinstance(model_in, dict)

print("REAL MAX BATCH-2: START", flush=True)

result = np.asarray(
    infer_max_batch(model_in, model_in),
    dtype=np.float32
)

print("ACTUAL MAX OUTPUT SHAPE:", result.shape, flush=True)

assert result.shape == (2, 2048)
assert np.isfinite(result).all()
assert np.allclose(result[0], result[1], atol=1e-5)

print("ONE REAL MAX BATCH CALL: PASS", flush=True)
print("OUTPUT SHAPE (2,2048): PASS", flush=True)
print("BOTH OUTPUTS FINITE: PASS", flush=True)
print("DUPLICATE INPUT PARITY: PASS", flush=True)
print("REAL MAX BATCH-2: PASS", flush=True)
PY

RC=$?
set -e

echo "=== EXECUTION RESULTS ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
tail -45 "$LOG"

if [ "$RC" -eq 0 ] && grep -q 'REAL MAX BATCH-2: PASS' "$LOG"; then
  echo "REAL MAX BATCH-2 VALIDATION: PASS"
else
  echo "REAL MAX BATCH-2 VALIDATION: FAIL"
fi

echo "WORKING NATIVE RELEASE: UNCHANGED"
echo "ORIGINAL DS CODE: UNCHANGED"
echo "GPU EXECUTION: NOT PERFORMED"

exit "$RC"
SH
