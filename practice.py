python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/core-artifact/pipeline.py")
src = p.read_text()
tree = ast.parse(src)

methods = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.FunctionDef)
    and n.name == "preprocess"
]

assert len(methods) == 1, "Expected one preprocess method"
fn = methods[0]

print("=== ORIGINAL MODEL INPUT CONSTRUCTION ===")
count = 0

for n in ast.walk(fn):
    value = None

    if isinstance(n, ast.Assign):
        targets = n.targets
        value = n.value
    elif isinstance(n, ast.AnnAssign):
        targets = [n.target]
        value = n.value
    else:
        continue

    for target in targets:
        text = ast.unparse(target)

        if text == "model_in":
            print(f"LINE {n.lineno}: model_in initialized")
            if isinstance(value, ast.Dict):
                for key, val in zip(value.keys, value.values):
                    print(" ", ast.unparse(key) if key else "**",
                          "<-", ast.unparse(val)[:160])
            else:
                print(" SOURCE:", ast.unparse(value)[:350])
            count += 1

        elif text.startswith("model_in["):
            print(f"LINE {n.lineno}: {text}")
            print(" VALUE:", ast.unparse(value)[:180])
            count += 1

print("\nMODEL INPUT ASSIGNMENTS FOUND:", count)

print("\n=== MODEL INPUT READS IN INFERENCE ===")
for n in ast.walk(tree):
    if isinstance(n, ast.FunctionDef) and n.name == "inference":
        keys = sorted({
            a.args[0].value
            for a in ast.walk(n)
            if isinstance(a, ast.Call)
            and isinstance(a.func, ast.Attribute)
            and isinstance(a.func.value, ast.Name)
            and a.func.value.id == "model_in"
            and a.func.attr == "get"
            and a.args
            and isinstance(a.args[0], ast.Constant)
            and isinstance(a.args[0].value, str)
        })
        for key in keys:
            print(" ", key)

print("\nREAD ONLY — NO FILES MODIFIED")
PY
