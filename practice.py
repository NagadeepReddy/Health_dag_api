cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
set -e

python3 - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")

graph = base / "grecbase_fusion_order_correct_max.py"
runner = base / "run_real_sanity_max_full.py"

new_graph = base / "grecbase_fusion_full_head_72_max.py"
new_runner = base / "run_real_sanity_full_head_72.py"

assert not new_graph.exists(), "STOP: Final graph already exists"
assert not new_runner.exists(), "STOP: Final runner already exists"

g = graph.read_text()
r = runner.read_text()

# Replace the 2048 reference output adapter
# with the existing native MAX final task head.
old_head = "grecbase_get_path_reference_max"
new_head = "grecbase_get_path_max"

assert g.count(old_head) == 3, "STOP: Unexpected head wiring"

g = g.replace(old_head, new_head)

# Reuse the working 72-input runner.
old_import = "grecbase_fusion_order_correct_max"
new_import = "grecbase_fusion_full_head_72_max"

assert r.count(old_import) == 1, "STOP: Unexpected graph import"

r = r.replace(old_import, new_import)

# Save actual final model output for later E2E validation.
marker = "    if result.shape == (1, 10819):"
assert r.count(marker) == 1, "STOP: Unexpected output block"

r = r.replace(
    marker,
    marker + """
        final_path = BASE / "real_sanity_max_10819_latest.npy"
        np.save(final_path, result)
        print("FINAL HEAD OUTPUT SAVED:", final_path)
""",
    1
)

ast.parse(g)
ast.parse(r)

new_graph.write_text(g)
new_runner.write_text(r)

print("FINAL MAX GRAPH: READY")
print("EXISTING TRAINED HEAD: REUSED")
print("72-INPUT GRAPH: PRESERVED")
print("ORIGINAL FILES: UNCHANGED")
print("PYTHON SYNTAX: PASS")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_full_head_72.py
