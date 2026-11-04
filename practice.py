cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import ast
from pathlib import Path

files = [
    Path("artifacts/v1.472/core-artifact/pipeline.py"),
    Path("artifacts/v1.472/utils/dependency-utils/models.py"),
]

print("=== PZAAS ORIGINAL PYTORCH EXECUTION CONTRACT ===")

for path in files:
    print("\nFILE:", path)
    if not path.is_file():
        print("NOT FOUND")
        continue

    source = path.read_text(errors="replace")
    lines = source.splitlines()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print("PARSE ERROR:", e)
        continue

    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        name = node.name.lower()
        if any(x in name for x in (
            "loadbase", "loadmodel", "grecbase",
            "predict", "inference"
        )):
            print(
                f"\n{node.__class__.__name__}: {node.name} "
                f"LINES {node.lineno}-{node.end_lineno}"
            )
            for i in range(node.lineno - 1,
                           min(node.end_lineno, node.lineno + 55)):
                print(f"{i+1}: {lines[i]}")

    print("\nRELEVANT IMPORTS / MODEL CALLS:")
    count = 0
    for i, line in enumerate(lines, 1):
        if any(x in line for x in (
            "GRecBase", "torch.load(", "loadBaseModel(",
            "loadModel(", "model.eval()", "model_params_path"
        )):
            print(f"{i}: {line[:230]}")
            count += 1
            if count >= 30:
                break

print("\nORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")
print("NEXT: REPLAY ORIGINAL PYTORCH ON SAVED EXACT INPUT")
PY
