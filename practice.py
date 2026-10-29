python3 -S -B - <<'PY'
from pathlib import Path
import ast

root = Path("/application1/cta_max_native_release_candidate_20261028")

files = (
    "cta_native_scheduler.py",
    "cta_worker_adapter.py",
    "cta_scheduler_factory.py",
)

for filename in files:
    p = root / filename
    assert p.is_file(), f"STOP: Missing {p}"

    source = p.read_text()
    tree = ast.parse(source)
    lines = source.splitlines()

    print(f"\n=== {filename} ===")

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        if node.name not in (
            "__init__",
            "run_iteration",
            "predict",
            "predict_batch",
            "create_cta_scheduler",
        ):
            continue

        print(f"\nFUNCTION: {node.name} | line {node.lineno}")

        for lineno in range(node.lineno, node.end_lineno + 1):
            line = lines[lineno - 1]
            if (
                lineno == node.lineno
                or any(term in line for term in (
                    "max_items_per_iteration",
                    "adapter.predict",
                    "predict_batch",
                    "pipeline.predict",
                    "request_queue",
                    "drainer",
                    "processed",
                    "batch",
                    "return",
                ))
            ):
                print(f"{lineno}: {line.strip()[:180]}")

    batch_names = sorted({
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and "batch" in node.name.lower()
    })
    print("EXPLICIT BATCH METHODS:", batch_names or "NONE")

print("\nTRUE BATCHING REVIEW: COMPLETE")
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("DS CODE: UNCHANGED")
PY
