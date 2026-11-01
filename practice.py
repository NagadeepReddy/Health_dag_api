cd /application1/sajjna8/rt-pzai-bplan-v1 && python3 - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.113/utils/dependency-utils/models.py")
src = p.read_text().splitlines()
tree = ast.parse("\n".join(src))

for cls in ast.walk(tree):
    if isinstance(cls, ast.ClassDef) and cls.name in ("GRecBase", "GRecTransfer"):
        print(f"\n=== {cls.name} (line {cls.lineno}) ===")
        for fn in cls.body:
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                print(f"{fn.name}: lines {fn.lineno}-{fn.end_lineno}")
                if cls.name == "GRecTransfer" and fn.name == "forward":
                    print("--- FORWARD CODE ---")
                    for i in range(fn.lineno - 1, fn.end_lineno):
                        print(f"{i+1}: {src[i]}")
PY
