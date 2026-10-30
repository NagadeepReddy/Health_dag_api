PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast
from pathlib import Path

roots = [
    Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"),
    Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
]

graph = roots[0] / "grecbase_fusion_batch2_draft.py"

assert graph.is_file(), "STOP: Active candidate graph missing"

print("=== BATCH-2 RESHAPE ROOT CAUSE ===")
print("GRAPH:", graph)

seen = set()
suspects = []

for root in roots:
    for path in root.rglob("*.py"):
        if path in seen or path.stat().st_size > 500000:
            continue
        seen.add(path)

        try:
            source = path.read_text()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeError):
            continue

        lines = source.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            fn = node.func
            name = (
                fn.attr if isinstance(fn, ast.Attribute)
                else fn.id if isinstance(fn, ast.Name)
                else ""
            )

            if name != "reshape":
                continue

            expression = ast.get_source_segment(source, node) or ""
            compact = "".join(expression.split())

            batch_one = any(x in compact for x in (
                "[1,1,1,1]", "(1,1,1,1)",
                "shape=[1,1,1,1]"
            ))

            length_related = any(x in expression.lower() for x in (
                "valid_length", "seq_len", "length",
                "batch_size"
            ))

            if batch_one or length_related:
                suspects.append((
                    path, node.lineno,
                    "BATCH-1 RESHAPE" if batch_one
                    else "LENGTH RESHAPE",
                    expression
                ))

print("=== SUSPECT OPERATIONS ===")

for path, line, reason, expression in suspects[:35]:
    print(f"\n{reason}: {path}:{line}")
    print(expression[:700])

print("\n=== ACTIVE GRAPH IMPORTS ===")
tree = ast.parse(graph.read_text())

for node in tree.body:
    if isinstance(node, ast.ImportFrom):
        print(node.module, "=>",
              [alias.name for alias in node.names])

print("\nSUSPECT COUNT:", len(suspects))
print("FILES MODIFIED: NONE")
print("CONTAINERS RESTARTED: NONE")
print("ORIGINAL DS: UNCHANGED")
PY
