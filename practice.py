POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
NAME=cta-batch2-trace-8766-10g

STATE=$("${POD[@]}" inspect --format '{{.State.Status}}' "$NAME" 2>/dev/null) || {
  echo "STOP: Isolated container not found"
  exit 1
}

echo "CONTAINER STATE: $STATE"

if [ "$STATE" != "running" ]; then
  echo "STOP: Container not running; no restart attempted"
else
"${POD[@]}" exec -i \
  -e PYTHONDONTWRITEBYTECODE=1 \
  "$NAME" /opt/venv/bin/python -B - <<'PY'
import ast
import os
import sys
import importlib.util
from pathlib import Path

print("=== ACTUAL NATIVE BATCH-2 RUNTIME ===")
print("CWD:", os.getcwd())
print("PYTHONPATH:", os.environ.get("PYTHONPATH"))

spec = importlib.util.find_spec("cta_max")
print("CTA PACKAGE:", spec.origin if spec else "NOT FOUND")
print("CTA SEARCH PATH:", list(spec.submodule_search_locations or []) if spec else [])

roots = [
    Path("/batch2/cta_max"),
    Path("/workspace/artifacts/v1.168-max/cta_max"),
    Path("/workspace/cta_max")
]

names = [
    "grecbase_fusion_batch2_draft.py",
    "grecbase_aux_features_max.py",
    "grecbase_aux_branches_max.py",
    "parallel_transformer_block_2layers.py",
    "nlp_bert_in_graph.py"
]

for root in roots:
    for name in names:
        path = root / name
        if not path.is_file():
            continue

        print("\nFILE:", path)
        source = path.read_text(errors="replace")

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            print("SYNTAX ERROR:", e)
            continue

        print("SYNTAX: PASS")

        suspects = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "reshape" or len(node.args) < 2:
                continue

            shape = ast.unparse(node.args[1])
            compact = shape.replace(" ", "")

            if compact.startswith(("[1,", "(1,")):
                suspects.append((node.lineno, shape))

        print("BATCH-1 RESHAPES:", len(suspects))
        for line, shape in suspects[:15]:
            print(f"  LINE {line}: {shape}")

        if name == "grecbase_fusion_batch2_draft.py":
            for i, line in enumerate(source.splitlines(), 1):
                if (
                    "_cta_batch2_aux_path" in line
                    or "module_from_spec" in line
                    or "exec_module" in line
                ):
                    print(f"IMPORT {i}: {line.strip()}")

print("\nORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
print("FILES MODIFIED: NONE")
print("CONTAINERS RESTARTED: NONE")
print("NEXT: FIX VERIFIED ACTIVE CALL SITE")
PY
fi
