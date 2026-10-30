PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast
from pathlib import Path

root = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)

assert root.is_dir(), "STOP: Batch-2 candidate missing"

hits = []
print("=== BATCH-2 RESHAPE TARGET CHECK ===")

for path in sorted(root.rglob("*.py")):
    if path.stat().st_size > 500000:
        continue

    source = path.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        continue

    lines = source.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        fn = node.func
        if not (
            isinstance(fn, ast.Attribute)
            and fn.attr == "reshape"
            and len(node.args) >= 2
        ):
            continue

        target = node.args[1]

        if not isinstance(target, (ast.List, ast.Tuple)):
            continue

        elements = target.elts
        if len(elements) != 2:
            continue

        first = elements[0]
        if not (
            isinstance(first, ast.Constant)
            and first.value == 1
        ):
            continue

        shape = ast.get_source_segment(source, target) or ""
        expression = ast.get_source_segment(source, node) or ""

        second = elements[1]
        likely = (
            isinstance(second, ast.Constant)
            and second.value == 128
        ) or (
            isinstance(second, ast.Name)
            and second.id in (
                "seq_len", "length", "hidden_size",
                "context_size", "dim"
            )
        )

        hits.append((path, node.lineno, shape, expression, likely))

hits.sort(key=lambda x: (not x[4], str(x[0]), x[1]))

for path, lineno, shape, expression, likely in hits[:30]:
    print("\nFILE:", path)
    print("LINE:", lineno)
    print("TARGET:", shape)
    print("PRIORITY:", "HIGH" if likely else "REVIEW")
    for i in range(max(1, lineno - 4),
                   min(len(path.read_text().splitlines()),
                       node_end := lineno + 4) + 1):
        print(f"{i}: {path.read_text().splitlines()[i-1]}")

print("\nMATCHES:", len(hits))
print("FILES MODIFIED: 0")
print("CONTAINERS RESTARTED: 0")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
PY
