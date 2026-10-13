set -e

python - <<'PY'
from pathlib import Path
import ast
import shutil

base = Path("artifacts/v1.168-max/cta_max")
path = base / "grecbase_fusion_order_correct_max.py"
runner = base / "run_real_sanity_max_full.py"

if not path.is_file() or not runner.is_file():
    raise SystemExit("STOP: Actual MAX graph or full runner missing")

source = path.read_text()
tree = ast.parse(source)

old_order = [
    "seq", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]

correct_order = [
    "seq", "context", "search0", "search1",
    "jet", "ihq", "sibling", "task"
]

matches = []

for node in ast.walk(tree):
    if not isinstance(node, ast.Assign):
        continue

    if not any(
        isinstance(t, ast.Name) and t.id == "outs"
        for t in node.targets
    ):
        continue

    value = node.value
    if not (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Attribute)
        and value.func.attr == "concat"
        and value.args
        and isinstance(value.args[0], ast.ListComp)
    ):
        continue

    comp = value.args[0]
    if len(comp.generators) != 1:
        continue

    items = comp.generators[0].iter
    if not isinstance(items, ast.List):
        continue

    names = [
        x.id for x in items.elts
        if isinstance(x, ast.Name)
    ]

    if names == old_order:
        matches.append(items)
    elif names == correct_order:
        print("ACTUAL GRAPH ALREADY HAS CORRECT ORDER")
        print("NO CHANGES NEEDED")
        raise SystemExit(0)

if len(matches) != 1:
    raise SystemExit(
        "STOP: Actual fusion expression differs from "
        "previously verified source. No files changed."
    )

items = matches[0]
lines = source.splitlines(keepends=True)

def offset(line, column):
    return sum(len(x) for x in lines[:line - 1]) + column

start = offset(items.lineno, items.col_offset)
end = offset(items.end_lineno, items.end_col_offset)

updated = (
    source[:start]
    + "[" + ", ".join(correct_order) + "]"
    + source[end:]
)

ast.parse(updated)

backup = path.with_suffix(".py.before_real_fusion_order_fix")
if not backup.exists():
    shutil.copy2(path, backup)

path.write_text(updated)

print("ACTUAL MAX FUSION GRAPH CORRECTED")
print("NEW ORDER:", " → ".join(correct_order))
print("BACKUP:", backup)
print("ORIGINAL PYTORCH / DS / CHECKPOINT UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
