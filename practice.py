cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import ast, hashlib
from pathlib import Path

roots = {
    "PZAAS": Path("artifacts/v1.472/utils/dependency-utils/models.py"),
    "CTA": Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168/utils/dependency-utils/models.py")
}
results = {}
for name, path in roots.items():
    tree = ast.parse(path.read_text())
    results[name] = {
        n.name: n for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef)
        and n.name in ("GRecBase", "GRecTransfer")
    }

for cls in ("GRecBase", "GRecTransfer"):
    print(f"\n=== {cls} ===")
    a = results["PZAAS"].get(cls)
    b = results["CTA"].get(cls)
    if not a or not b:
        print("Missing:", "PZAAS" if not a else "CTA")
        continue
    for name, node in (("PZAAS", a), ("CTA", b)):
        methods = [x for x in node.body if isinstance(x, ast.FunctionDef)]
        print(name, "bases:", [ast.unparse(x) for x in node.bases])
        print(name, "methods:", [x.name for x in methods])
    for method in ("__init__", "forward"):
        def digest(node):
            fn = next((x for x in node.body if isinstance(x, ast.FunctionDef) and x.name == method), None)
            return hashlib.sha256(ast.dump(fn, include_attributes=False).encode()).hexdigest()[:12] if fn else "missing"
        print(method, "MATCH" if digest(a) == digest(b) else "DIFFERENT")
PY
