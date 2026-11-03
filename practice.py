cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

root = Path("artifacts/v1.472-max/pzaas_max")
manifest = json.loads(
    (root/"pzaas_base_weights/manifest.json").read_text()
)

modules = {
    "grecbase_aux_branches_max.py": "",
    "main_context_max.py": "context_head.",
    "sibling_context_max.py": "sibling_context_head.",
}

updates = {}

for filename, prefix in modules.items():
    p = root / filename
    source = p.read_text()
    tree = ast.parse(source)

    if prefix and not any(k.startswith(prefix) for k in manifest):
        raise SystemExit(f"STOP: Missing weight group {prefix}")

    loads = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "np"
        and n.func.attr == "load"
    ]

    if not loads and "load_weight(" in source:
        print("ALREADY WIRED:", filename)
        continue

    if len(loads) != 1:
        raise SystemExit(f"STOP: Unexpected load count in {filename}")

    old = ast.get_source_segment(source, loads[0])
    if "WDIR" not in old or "name" not in old:
        raise SystemExit(f"STOP: Unexpected load in {filename}")

    new = (
        f'load_weight("{prefix}" + name)'
        if prefix else 'load_weight(name)'
    )

    if source.count(old) != 1:
        raise SystemExit(f"STOP: Non-unique load in {filename}")

    source = source.replace(old, new, 1)

    imp = "from pzaas_max.pzaas_weight_loader import load_weight\n"
    if imp not in source:
        parsed = ast.parse(source)
        lines = source.splitlines(keepends=True)
        pos = 0
        if parsed.body and isinstance(parsed.body[0], ast.Expr):
            value = parsed.body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                pos = parsed.body[0].end_lineno
        for n in parsed.body:
            if isinstance(n, ast.ImportFrom) and n.module == "__future__":
                pos = max(pos, n.end_lineno)
        lines.insert(pos, imp)
        source = "".join(lines)

    compile(source, str(p), "exec")
    updates[p] = source

for p, source in updates.items():
    p.write_text(source)
    print("WIRED:", p.name)

print("\nPZAAS THREE-MODULE WEIGHT WIRING: PASS")
print("SYNTAX: PASS")
print("GET_PATH / NLP / DIMENSIONS: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
