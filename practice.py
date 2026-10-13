python - <<'PY'
from pathlib import Path
import ast

root = Path("artifacts/v1.168")
pipeline = root / "core-artifact/pipeline.py"
models = root / "utils/dependency-utils/models.py"

for path in (pipeline, models):
    lines = path.read_text().splitlines()
    tree = ast.parse("\n".join(lines))
    print("\n===", path.name, "===")

    if path == pipeline:
        terms = ("model_base", "model_in", "model_response",
                 "get_path(", "predict_raw(", "remove_tasks_dense")
        hits = [i for i, s in enumerate(lines)
                if any(t in s for t in terms)]
        selected = set()
        for i in hits:
            selected.update(range(max(0, i-2), min(len(lines), i+4)))
        for i in sorted(selected):
            print(f"{i+1}: {lines[i][:180]}")
    else:
        for cls in ast.walk(tree):
            if isinstance(cls, ast.ClassDef) and cls.name == "GRecBase":
                for fn in cls.body:
                    if isinstance(fn, ast.FunctionDef) and fn.name in ("forward", "get_path"):
                        print(f"\nGRecBase.{fn.name}:")
                        for i in range(max(fn.lineno-1, fn.end_lineno-22), fn.end_lineno):
                            print(f"{i+1}: {lines[i][:180]}")

print("\nREAD ONLY — NOTHING MODIFIED")
PY
