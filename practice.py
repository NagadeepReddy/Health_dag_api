cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py")
source = p.read_text()

old = "sibling = ops.concat([ops.mean(sibling_stack, axis=1), ops.max(sibling_stack, axis=1)], axis=1)"

new = """sibling_valid_len = ops.cast(
        ops.reshape(remaining[65], [1, 1]), DType.float32
    )
    sibling_mean = ops.sum(sibling_stack, axis=1) / (
        sibling_valid_len
        + ops.constant(1e-7, dtype=DType.float32, device=device)
    )
    sibling = ops.concat(
        [sibling_mean, ops.max(sibling_stack, axis=1)],
        axis=1
    )"""

if source.count(old) != 1:
    raise SystemExit("STOP: Expected Sibling pooling expression not found exactly once. No changes.")

if source.count("sibling_inputs = remaining[25:65]") != 1:
    raise SystemExit("STOP: Sibling input mapping differs. No changes.")

updated = source.replace(old, new, 1)
ast.parse(updated)

backup = p.with_suffix(".py.before_sibling_pooling_fix")
if not backup.exists():
    shutil.copy2(p, backup)

p.write_text(updated)

print("ACTUAL MAX SIBLING POOLING UPDATED")
print("SUM / VALID LENGTH + MAX")
print("FUSION ORDER, PYTORCH, DS, WEIGHTS UNCHANGED")
print("BACKUP:", backup)
PY

if [ $? -eq 0 ]; then
  podman run --rm -i \
    -v "$PWD:/workspace" \
    -w /workspace \
    --entrypoint python \
    docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
    artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
fi
