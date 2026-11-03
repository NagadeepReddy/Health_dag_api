cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

r = Path("artifacts/v1.472-max/pzaas_max")
m = json.loads((r/"pzaas_base_weights/manifest.json").read_text())

modules = {
    "grecbase_aux_branches_max.py": "",
    "grecbase_get_path_max.py": "",
    "main_context_max.py": "context_head.",
    "sibling_context_max.py": "sibling_context_head.",
    "nlp_bert_in_graph.py": "nlp_encoder."
}

for filename, prefix in modules.items():
    p = r / filename
    print(f"\n=== {filename} ===")
    s = p.read_text()
    tree = ast.parse(s)
    seen = set()

    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        if not isinstance(n.func, ast.Name):
            continue
        if n.func.id not in ("weight", "embed"):
            continue

        call = ast.get_source_segment(s, n)
        if call in seen:
            continue
        seen.add(call)

        arg = n.args[-1] if n.args else None
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            name = arg.value
            matches = [k for k in (name, prefix + name) if k in m]
            print(n.lineno, call[:100], "=>", matches or "NEEDS MAPPING")
        else:
            print(n.lineno, call[:120], "=> DYNAMIC")

    print("UNIQUE CALLS:", len(seen))

print("\nMAPPING INSPECTION: COMPLETE")
print("NO FILES MODIFIED")
PY
