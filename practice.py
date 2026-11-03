cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, hashlib

roots = {
    "PZAAS": Path("artifacts/v1.472"),
    "CTA": Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168")
}

for name, root in roots.items():
    p = root/"utils/dependency-utils/models.py"
    print(f"\n=== {name} GRec ARCHITECTURE ===")
    if not p.is_file():
        print("Missing:", p)
        continue
    tree = ast.parse(p.read_text())
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name in ("GRecBase", "GRecTransfer", "GRec"):
            code = ast.dump(n, include_attributes=False)
            print(n.name, "line:", n.lineno,
                  "SHA:", hashlib.sha256(code.encode()).hexdigest()[:16])
            print("Methods:", [x.name for x in n.body
                  if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))][:25])
PY
