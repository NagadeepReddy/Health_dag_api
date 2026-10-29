cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
import ast
from pathlib import Path

files = [
    Path("artifacts/v1.168/core-artifact/pipeline.py"),
    Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py"),
]

for path in files:
    assert path.is_file(), f"STOP: Missing {path}"
    lines = path.read_text().splitlines()
    tree = ast.parse("\n".join(lines))

    print("\n=== FILE:", path, "===")

    names = {"predict_raw", "preprocess", "inference", "postprocess", "attach_max"}

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name not in names:
            continue

        args = [a.arg for a in node.args.args]
        print(f"\nFUNCTION: {node.name}({', '.join(args)})")
        print("LINES:", node.lineno, "-", node.end_lineno)

        if node.name in ("predict_raw", "attach_max"):
            selected = set()

            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                f = child.func
                called = (
                    f.attr if isinstance(f, ast.Attribute)
                    else f.id if isinstance(f, ast.Name)
                    else ""
                )
                if called in (
                    "preprocess", "inference", "postprocess",
                    "predict_raw", "attach_max", "infer_max_live",
                    "predict", "execute", "setattr"
                ):
                    selected.update(range(
                        max(node.lineno, child.lineno - 4),
                        min(node.end_lineno, child.end_lineno + 4) + 1
                    ))

            selected.update(range(
                node.lineno,
                min(node.lineno + 8, node.end_lineno) + 1
            ))

            selected.update(range(
                max(node.lineno, node.end_lineno - 9),
                node.end_lineno + 1
            ))

            for i in sorted(selected):
                print(f"{i}: {lines[i-1][:180]}")

print("\nREAL MAX BATCH-2 CPU: ALREADY PASSED")
print("NATIVE JSON BATCH CONNECTION: PENDING")
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
