cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
import ast
from pathlib import Path

files = [
    Path("artifacts/v1.168/core-artifact/pipeline.py"),
    Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py"),
]

for path in files:
    assert path.is_file(), f"STOP: Missing {path}"
    source = path.read_text()
    lines = source.splitlines()
    tree = ast.parse(source)

    print("\n=== FILE:", path, "===")

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        if path.name == "pipeline.py":
            if node.name not in ("predict_raw", "inference"):
                continue
        else:
            if node.name not in ("attach_max", "__call__"):
                continue

        print(f"\n=== FUNCTION {node.name} ===")
        print("SIGNATURE:", lines[node.lineno - 1].strip())

        if node.name == "predict_raw":
            # Full orchestration path, including data passed between stages.
            start, end = node.lineno, node.end_lineno
            for i in range(start, end + 1):
                if (
                    i <= start + 8
                    or any(k in lines[i - 1] for k in (
                        "preprocess(", "inference(", "postprocess(",
                        "return ", "model_in", "can_in",
                        "request_context", "task_in", "output"
                    ))
                ):
                    print(f"{i}: {lines[i - 1][:200]}")
        elif path.name == "cta_spawn_worker.py":
            for i in range(node.lineno, node.end_lineno + 1):
                print(f"{i}: {lines[i - 1][:200]}")

print("\nREAL MAX BATCH-2: ALREADY PASSED")
print("NATIVE BATCH DISPATCH MOCK: ALREADY PASSED")
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
