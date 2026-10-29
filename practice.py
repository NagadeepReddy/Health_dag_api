python3 -S -B - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
assert root.is_dir(), "STOP: MAX artifacts missing"

found = []

for p in root.rglob("*.py"):
    if "backup" in str(p).lower():
        continue

    try:
        source = p.read_text()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError):
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "MaxCTAInference":
            found.append((p, node, source.splitlines()))

assert found, "STOP: MaxCTAInference class not found"

keywords = (
    "execute(", "run(", "compile(", "load_model(",
    "batch", "shape", "reshape", "stack(",
    "concatenate(", "session", "forward(",
    "predict(", "infer(", "tensor",
)

for p, cls, lines in found:
    print("\n=== REAL MAX INFERENCE CLASS ===")
    print("FILE:", p)
    print("CLASS:", cls.name)

    print("\n=== METHODS ===")
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            print(f"{n.lineno}: {n.name}()")

    print("\n=== INFERENCE / BATCH / SHAPE OPERATIONS ===")
    count = 0

    for i in range(cls.lineno - 1, cls.end_lineno):
        line = lines[i]
        if any(k in line.lower() for k in keywords):
            print(f"{i+1}: {line.strip()[:200]}")
            count += 1

        if count >= 100:
            print("OUTPUT LIMITED TO 100 MATCHES")
            break

print("\nCLASS REVIEW: COMPLETE")
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
