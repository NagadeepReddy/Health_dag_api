cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

print("=== PZAAS SEQUENCE FEATURE IMPLEMENTATION ===")

roots = [
    Path("artifacts/v1.472"),
    Path("artifacts/v1.472-max/pzaas_max")
]

found = 0

for root in roots:
    for p in root.rglob("*.py"):
        try:
            src = p.read_text()
            if "FfMAP" not in src:
                continue
            tree = ast.parse(src)
        except (SyntaxError, UnicodeError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if "FfMAP" not in node.name:
                continue

            found += 1
            print("\nFILE:", p)
            print("CLASS:", node.name)

            lines = src.splitlines()

            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if method.name not in ("__init__", "forward", "__call__"):
                        continue

                    print("\nMETHOD:", method.name)
                    start = method.lineno
                    end = min(method.end_lineno, start + 105)

                    for i in range(start, end + 1):
                        print(f"{i}: {lines[i-1]}")

print("\nORIGINAL FEATURE CLASSES:", found)

print("\n=== RELEVANT PZAAS MODEL WEIGHTS ===")

base = Path("artifacts/v1.472-max/pzaas_max")
weights = sorted(base.rglob("*.npy"))

for p in weights:
    name = p.name.lower()
    if any(x in name for x in (
        "sequence", "embedding", "page",
        "item", "meta", "seq_dense"
    )):
        print(p.name)

print("\n=== AVAILABLE MAX SEQUENCE MODULES ===")

for p in sorted(base.glob("*.py")):
    if any(x in p.name.lower() for x in (
        "sequence", "transformer", "pooling"
    )):
        print(p.name)

print("\nSEQUENCE FEATURE CONTRACT: INSPECTED")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: IMPLEMENT MISSING MAX FEATURE COMPONENT")
PY
