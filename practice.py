cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast
import numpy as np

root = Path("artifacts/v1.472-max/pzaas_max")

print("=== PZAAS FINAL TWO BRANCHES ===")

with np.load(
    root / "validation/pzaas_eight_branch_targets.npz",
    allow_pickle=False
) as data:
    for key in data.files:
        if "seq" in key.lower() or "context" in key.lower():
            print("PYTORCH TARGET:", key, data[key].shape)

for name in [
    "main_context_max.py",
    "parallel_transformer_block_2layers.py",
    "grecbase_fusion_full_head_72_max.py"
]:
    p = root / name
    print("\nFILE:", p)
    if not p.is_file():
        print("NOT FOUND")
        continue

    source = p.read_text()
    tree = ast.parse(source)
    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if any(x in node.name.lower() for x in [
                "context", "sequence", "grecbase_fusion"
            ]):
                print("FUNCTION:", node.name,
                      "LINES:", node.lineno, "-", node.end_lineno)

    if name == "grecbase_fusion_full_head_72_max.py":
        print("\nSEQUENCE / CONTEXT GRAPH CALLS:")
        for i, line in enumerate(lines, 1):
            if any(x in line for x in [
                "main_context_forward",
                "ParallelTransformer",
                "features(",
                "postprocess(",
                "seq_dense",
                "context_inputs"
            ]):
                print(f"{i}: {line.strip()}")

print("\nFINAL TWO BRANCH MAPPING: INSPECTED")
print("ORIGINAL DS: UNCHANGED")
print("NEXT: REAL MAX SEQUENCE + CONTEXT PARITY")
PY
