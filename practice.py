cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

r = Path("artifacts/v1.472")
p = r / "core-artifact/pipeline.py"
s = p.read_text().splitlines()
tree = ast.parse("\n".join(s))

print("=== ORIGINAL DS MODEL INPUT FLOW ===")
for n in ast.walk(tree):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if n.name in ("preprocess", "inference"):
            print(f"\nFUNCTION: {n.name} | {n.lineno}-{n.end_lineno}")
            for x in ast.walk(n):
                if isinstance(x, ast.Return):
                    print("RETURN:", x.lineno,
                          ast.unparse(x.value)[:350] if x.value else "None")
                elif isinstance(x, ast.Call):
                    call = ast.unparse(x.func)
                    if any(t in call.lower() for t in
                           ("model_base", "model_sku", "preprocess", "torch.tensor")):
                        print("CALL:", x.lineno, ast.unparse(x)[:200])

print("\n=== SAVED MODEL INPUT CANDIDATES ===")
roots = [r, Path("artifacts/v1.472-max")]
count = 0
for root in roots:
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".npy", ".npz", ".pkl", ".pickle", ".pt"):
            if any(t in p.name.lower() for t in
                   ("input", "sample", "fixture", "model_in", "sanity")):
                print(p, "| bytes:", p.stat().st_size)
                count += 1
                if count >= 30:
                    break
    if count >= 30:
        break

print("MODEL INPUT INSPECTION: COMPLETE")
print("NO FILES MODIFIED")
PY
