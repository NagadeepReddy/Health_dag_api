PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, re
from pathlib import Path

root = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)

assert root.is_dir(), "STOP: Batch-2 candidate missing"

print("=== ACTIVE BATCH-2 RESHAPE INVESTIGATION ===")

priority = [
    "grecbase_fusion_batch2_draft.py",
    "grecbase_aux_features_max.py",
    "grecbase_aux_branches_max.py",
    "parallel_transformer_block_2layers.py",
    "nlp_bert_in_graph.py"
]

files = [root / n for n in priority if (root / n).is_file()]
files += [
    p for p in sorted(root.glob("*.py"))
    if p not in files
]

suspects = []

for path in files:
    source = path.read_text(errors="replace")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        continue

    lines = source.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if not isinstance(node.func, ast.Attribute):
            continue

        if node.func.attr != "reshape" or len(node.args) < 2:
            continue

        shape = ast.unparse(node.args[1])
        compact = re.sub(r"\s+", "", shape)

        if re.match(r"^\[1,", compact) and (
            "128" in compact
            or "dim" in compact
            or "256" in compact
        ):
            suspects.append((path, node.lineno, shape, lines))

print("SUSPECT RESHAPES:", len(suspects))

for path, number, shape, lines in suspects[:35]:
    print(f"\nFILE: {path.name}")
    print(f"LINE: {number}")
    print(f"SHAPE: {shape}")
    for i in range(max(0, number - 3),
                   min(len(lines), number + 2)):
        print(f"{i+1}: {lines[i]}")

print("\n=== GRAPH HELPER IMPORTS ===")
for name in priority[:3]:
    path = root / name
    if not path.is_file():
        continue
    print(f"\n{name}")
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if (
            "grecbase_aux" in line
            or "_cta_batch2_aux" in line
            or "parallel_transformer" in line
            or "nlp_bert" in line
        ):
            print(f"{i}: {line[:180]}")

print("\nORIGINAL MAX: UNCHANGED")
print("ORIGINAL DS: UNCHANGED")
print("FILES MODIFIED: 0")
print("CONTAINERS RESTARTED: 0")
print("NEXT: PATCH CONFIRMED CALL SITE ONLY")
PY
