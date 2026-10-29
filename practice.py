cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

files = [
    "grecbase_aux_branches_max_batch2_fix.py",
    "grecbase_fusion_full_head_72_max_batch2_auxfix.py",
    "main_context_max_batch2_fix.py",
    "nlp_bert_in_graph_batch2_contextfix.py",
]

total = 0

for name in files:
    p = dev / name
    print(f"\n=== {name} ===")

    if not p.is_file():
        print("MISSING — check before proceeding")
        continue

    source = p.read_text()
    tree = ast.parse(source)
    lines = source.splitlines()
    found = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "reshape" or len(node.args) < 2:
            continue

        shape = node.args[1]
        if not isinstance(shape, (ast.List, ast.Tuple)) or not shape.elts:
            continue

        first = shape.elts[0]
        if isinstance(first, ast.Constant) and first.value == 1:
            found.append((node.lineno, ast.unparse(node.args[0]),
                          ast.unparse(shape)))

    for line, value, shape in sorted(found):
        print(f"LINE {line} | TENSOR: {value[:65]} | SHAPE: {shape}")
        print("  SOURCE:", lines[line - 1].strip()[:180])

    print("REMAINING LEADING-1 RESHAPES:", len(found))
    total += len(found)

print("\nTOTAL CANDIDATES:", total)
print("AUDIT ONLY — NOT ALL CANDIDATES REQUIRE CHANGES")
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
