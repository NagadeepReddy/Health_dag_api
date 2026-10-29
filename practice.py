python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_max/run_live_max_inference.py"
)

assert p.is_file(), f"STOP: File missing: {p}"

source = p.read_text()
tree = ast.parse(source)
lines = source.splitlines()

print("=== REAL MAX EXECUTION ===")
print("FILE:", p)

functions = [
    n for n in ast.walk(tree)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
]

for n in functions:
    print(f"FUNCTION: {n.name} | {n.lineno}-{n.end_lineno}")

targets = [
    n for n in functions
    if n.name == "infer_max_live"
]

assert len(targets) == 1, "STOP: infer_max_live not uniquely found"

n = targets[0]

print("\n=== infer_max_live IMPLEMENTATION ===")
for i in range(n.lineno, min(n.end_lineno, n.lineno + 179) + 1):
    print(f"{i}: {lines[i-1]}")

print("\n=== SHAPE / GRAPH / SESSION REFERENCES ===")
terms = (
    "batch", "shape", "compile", "session",
    "execute", "infer", "tensor", "reshape",
    "stack", "concatenate", "model_in"
)

shown = 0
for i, line in enumerate(lines, 1):
    if any(t in line.lower() for t in terms):
        print(f"{i}: {line[:180]}")
        shown += 1
        if shown >= 60:
            print("OUTPUT LIMITED TO 60 MATCHES")
            break

print("\nFILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("DS CODE: UNCHANGED")
PY
