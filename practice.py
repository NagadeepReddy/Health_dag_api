cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py")
source = p.read_text()

old = "sibling = ops.concat([ops.mean(sibling_stack, axis=1), ops.max(sibling_stack, axis=1)], axis=1)"

new = (
    "sibling = ops.concat(["
    "ops.sum(sibling_stack, axis=1) / "
    "(ops.cast(ops.reshape(remaining[65], [1, 1]), DType.float32) "
    "+ ops.constant(1e-7, dtype=DType.float32, device=device)), "
    "ops.max(sibling_stack, axis=1)"
    "], axis=1)"
)

if source.count(old) != 1:
    raise SystemExit("STOP: Expected original pooling line not found. No changes.")

if "sibling_inputs = remaining[25:65]" not in source:
    raise SystemExit("STOP: Input mapping differs. No changes.")

updated = source.replace(old, new, 1)
ast.parse(updated, filename=str(p))

backup = p.with_suffix(".py.before_sibling_pooling_fix")
if not backup.exists():
    shutil.copy2(p, backup)

p.write_text(updated)

print("SIBLING POOLING FIXED IN ACTUAL MAX GRAPH")
print("PYTHON SYNTAX: PASS")
print("ORIGINAL PYTORCH AND WEIGHTS UNCHANGED")
PY

if [ $? -eq 0 ]; then
  podman run --rm -i \
    -v "$PWD:/workspace" \
    -w /workspace \
    --entrypoint python \
    docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
    artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
fi
