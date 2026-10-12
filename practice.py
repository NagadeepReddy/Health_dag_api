python - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")

files = [
    root / "utils/dependency-utils/models.py",
    base / "grecbase_get_path_max.py",
    base / "grecbase_fusion_real_shapes_max.py",
]

for path in files:
    assert path.is_file(), path
    source = path.read_text()
    lines = source.splitlines()
    tree = ast.parse(source)

    print("\n====", path.name, "====")

    if path.name == "models.py":
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            if cls.name != "GRecBase":
                continue
            for fn in cls.body:
                if not isinstance(fn, ast.FunctionDef):
                    continue
                if fn.name == "get_path":
                    print("ORIGINAL GRecBase.get_path:")
                    for i in range(fn.lineno, fn.end_lineno + 1):
                        print(f"{i}: {lines[i-1]}")
                elif fn.name == "forward":
                    for n in ast.walk(fn):
                        if isinstance(n, ast.Return):
                            print(
                                "ORIGINAL FORWARD RETURN:",
                                ast.unparse(n.value)
                            )
    else:
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef):
                continue
            if path.name == "grecbase_get_path_max.py":
                if fn.name == "grecbase_get_path_max":
                    print("MAX GET_PATH:")
                    for i in range(fn.lineno, fn.end_lineno + 1):
                        print(f"{i}: {lines[i-1]}")
            else:
                print("MAX FUSION OUTPUT:")
                for n in ast.walk(fn):
                    if isinstance(n, ast.Call):
                        expr = ast.unparse(n.func)
                        if (
                            "get_path" in expr
                            or expr.endswith(".output")
                        ):
                            print(ast.unparse(n)[:350])

print("\nREAD ONLY — NOTHING MODIFIED")
PY
