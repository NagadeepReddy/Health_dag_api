cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path("artifacts/v1.472-max/pzaas_max")

total = 0
print("=== REMAINING MAX WEIGHT LOADS ===")

for p in sorted(root.glob("*.py")):
    if p.name == "pzaas_weight_loader.py":
        continue

    source = p.read_text()
    tree = ast.parse(source)
    hits = []

    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            fn = ast.unparse(n.func)
            if fn in ("np.load", "torch.load"):
                hits.append((n.lineno, ast.get_source_segment(source, n)))

    if hits:
        print(f"\nFILE: {p.name}")
        for line, expr in sorted(hits):
            print(f"  {line}: {expr[:180]}")
            total += 1

    legacy = [
        (i, line.strip()) for i, line in
        enumerate(source.splitlines(), 1)
        if any(x in line for x in (
            "v1.168", "grecbase_integration_weights",
            "cta_max/", "WDIR ="
        ))
    ]
    for line, value in legacy[:8]:
        print(f"  LEGACY {line}: {value[:150]}")

print("\nREMAINING NUMPY/TORCH LOAD CALLS:", total)
print("AUDIT COMPLETE — NO FILES MODIFIED")
PY
