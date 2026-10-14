python3 - <<'PY'
import ast
from pathlib import Path

cases = [
    ("ORIGINAL PYTORCH",
     "artifacts/v1.168/utils/dependency-utils/models.py",
     "ParallelTransformerBlock",
     {"forward", "create_key_padding_mask", "get_mask"}),
    ("ACTIVE MAX",
     "artifacts/v1.168-max/cta_max/parallel_transformer_block_2layers.py",
     "ParallelTransformerBlockMAX",
     {"__call__"}),
]

terms = ("mask", "valid", "score", "softmax", "attn",
         "norm", "ff", "rotary", "residual", "position")

for label, filename, classname, methods in cases:
    p = Path(filename)
    lines = p.read_text().splitlines()
    tree = ast.parse("\n".join(lines))
    classes = [n for n in ast.walk(tree)
               if isinstance(n, ast.ClassDef) and n.name == classname]

    print("\n===", label, "===")
    if not classes:
        print("CLASS NOT FOUND:", classname)
        continue

    for cls in classes:
        for fn in cls.body:
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if fn.name not in methods:
                continue
            print("METHOD:", fn.name)
            for i in range(fn.lineno, fn.end_lineno + 1):
                line = lines[i - 1]
                if any(term in line.lower() for term in terms):
                    print(f"{i}: {line}")

print("\nREAD-ONLY COMPARISON COMPLETE")
PY
