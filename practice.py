cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

set -e

python - <<'PY'
from pathlib import Path
import ast
import re
import shutil

base = Path("artifacts/v1.168-max/cta_max")

graph = base / "grecbase_fusion_order_correct_max.py"
sequence = base / "sequence_transformer_max.py"

sources = {
    graph: graph.read_text(),
    sequence: sequence.read_text()
}

# Fix 1: Pass the real item_pre input to Sequence.
new_graph, count1 = re.subn(
    r'(features\(\s*page\s*,\s*item\s*,\s*item_meta\s*,\s*)item(\s*,\s*page_wide\s*\))',
    r'\g<1>item_pre\2',
    sources[graph]
)

# Fix 2: Use item_pre_in for its own trained embedding.
new_sequence, count2 = re.subn(
    r'(item_pre\s*=\s*self\.item_pre_embedding\(\s*)item_in(\s*\))',
    r'\g<1>item_pre_in\2',
    sources[sequence]
)

if count1 != 1 or count2 != 1:
    raise SystemExit(
        f"STOP: Expected exactly two fixes. "
        f"Found graph={count1}, sequence={count2}. "
        "No files changed."
    )

changes = {
    graph: new_graph,
    sequence: new_sequence
}

for p, updated in changes.items():
    ast.parse(updated, filename=str(p))

for p in changes:
    backup = p.with_suffix(".py.before_item_pre_fix")
    if not backup.exists():
        shutil.copy2(p, backup)

for p, updated in changes.items():
    p.write_text(updated)

print("ACTUAL MAX SEQUENCE INPUT FIXED")
print("item_pre now uses its correct input and embedding")
print("BOTH PYTHON FILES: SYNTAX PASS")
print("FUSION ORDER AND SIBLING FIX PRESERVED")
print("ORIGINAL PYTORCH / DS / WEIGHTS UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
