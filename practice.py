cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast
import re

root = Path("artifacts/v1.472")

print("=== PZAAS MODEL LOADING VERIFICATION ===")

names = {
    "loadBaseModel",
    "loadTransformerModel",
    "loadModel",
}

patterns = re.compile(
    r"load_state_dict|strict\s*=|torch\.load|"
    r"num_layers|ptransformer|model_base\s*="
)

files = [
    root / "core-artifact/pipeline.py",
    root / "utils/dependency-utils/models.py",
]

for p in files:
    if not p.is_file():
        continue

    print("\nFILE:", p)
    lines = p.read_text(errors="replace").splitlines()

    try:
        tree = ast.parse("\n".join(lines))
    except SyntaxError as exc:
        print("AST ERROR:", exc)
        continue

    functions = [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and n.name in names
    ]

    for node in functions:
        print("\nLOADER:", node.name)
        for i in range(node.lineno-1, min(node.end_lineno, len(lines))):
            print(f"{i+1}: {lines[i]}")

    print("\nOTHER RELEVANT LINES:")
    for i, line in enumerate(lines):
        if patterns.search(line):
            if not any(n.lineno <= i+1 <= n.end_lineno for n in functions):
                print(f"{i+1}: {line.strip()[:180]}")

print("\n=== RESULT ===")
print("ORIGINAL DS: UNCHANGED")
print("MAX GRAPH: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: CONFIRM RUNTIME DEPTH BEFORE ALIGNMENT")
PY
