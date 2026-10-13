cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py")
runner = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py")

if not p.is_file() or not runner.is_file():
    raise SystemExit("STOP: Actual MAX graph or runner missing")

source = p.read_text()
tree = ast.parse(source)

old = ["seq", "context", "search0", "search1",
       "task", "jet", "ihq", "sibling"]

correct = ["seq", "context", "search0", "search1",
           "jet", "ihq", "sibling", "task"]

lines = source.splitlines(keepends=True)

def offset(line, col):
    return sum(map(len, lines[:line-1])) + col

def branch_name(expr):
    if isinstance(expr, ast.Name):
        return expr.id
    if (isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Attribute)
        and expr.func.attr == "reshape"
        and expr.args):
        return branch_name(expr.args[0])
    return None

changes = []

for node in ast.walk(tree):
    if not isinstance(node, ast.Assign):
        continue
    if not any(isinstance(t, ast.Name) and t.id == "outs"
               for t in node.targets):
        continue

    call = node.value
    if not (isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr in ("stack", "concat")
            and call.args):
        continue

    container = call.args[0]

    if isinstance(container, ast.ListComp):
        if len(container.generators) != 1:
            continue
        container = container.generators[0].iter

    if not isinstance(container, (ast.List, ast.Tuple)):
        continue

    names = [branch_name(x) for x in container.elts]

    if names == correct:
        print("FUSION ORDER ALREADY CORRECT — NO CHANGE")
        continue

    if names != old:
        continue

    exprs = {
        name: ast.get_source_segment(source, expr)
        for name, expr in zip(names, container.elts)
    }

    bracket = ("[", "]") if isinstance(container, ast.List) else ("(", ")")
    replacement = bracket[0] + ", ".join(exprs[n] for n in correct) + bracket[1]

    changes.append((
        offset(container.lineno, container.col_offset),
        offset(container.end_lineno, container.end_col_offset),
        replacement
    ))

if not changes:
    print("NO OLD-ORDER FUSION EXPRESSION FOUND")
    print("No source changed. Do not repeat fusion-order work.")
else:
    updated = source
    for start, end, replacement in sorted(changes, reverse=True):
        updated = updated[:start] + replacement + updated[end:]

    ast.parse(updated)

    backup = p.with_suffix(".py.before_actual_order_fix")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(updated)
    print("ACTUAL MAX GRAPH CORRECTED")
    print("ORDER:", " -> ".join(correct))
    print("BACKUP:", backup)

print("ORIGINAL PYTORCH / DS / WEIGHTS UNCHANGED")
PY
