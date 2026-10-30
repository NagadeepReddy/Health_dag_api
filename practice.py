python3 -B - <<'PY'
from pathlib import Path
import ast

repo = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1"
)
native = repo / "artifacts/v1.168-max/maxserve_cta_extension"
dev = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2"
)

files = {
    "NATIVE ADAPTER": native / "cta_worker_adapter.py",
    "NATIVE SCHEDULER": native / "cta_native_scheduler.py",
    "NATIVE FACTORY": native / "cta_scheduler_factory.py",
    "NATIVE WORKER HOOK": native / "cta_worker_registration.py",
    "DEV BATCH ADAPTER": dev / "cta_worker_adapter.py",
    "DEV BATCH SCHEDULER": dev / "cta_native_scheduler.py",
}

results = {}

for label, path in files.items():
    print("\n====", label, "====")

    if not path.is_file():
        print("MISSING:", path)
        results[label] = None
        continue

    source = path.read_text()
    tree = ast.parse(source)
    lines = source.splitlines()

    methods = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    print("SYNTAX: PASS")
    print("predict_batch:", "predict_batch" in methods)
    print("run_iteration:", "run_iteration" in methods)

    keywords = (
        "predict_batch",
        "batch_fn",
        "max_items_per_iteration",
        "run_iteration",
        "load_scheduler",
        "cta_native_scheduler",
        "cta_worker_adapter",
        "CTA_NATIVE_BATCH_DISPATCH",
    )

    matches = [
        (i, line.strip())
        for i, line in enumerate(lines, 1)
        if any(word in line for word in keywords)
    ]

    for number, line in matches[:18]:
        print(f"{number}: {line[:160]}")

    results[label] = {
        "methods": methods,
        "source": source,
    }

native_adapter = results.get("NATIVE ADAPTER")
native_scheduler = results.get("NATIVE SCHEDULER")
dev_adapter = results.get("DEV BATCH ADAPTER")
dev_scheduler = results.get("DEV BATCH SCHEDULER")

print("\n==== NATIVE BATCHING READINESS ====")

if not all((
    native_adapter,
    native_scheduler,
    dev_adapter,
    dev_scheduler,
)):
    print("STATUS: REQUIRED COMPONENT MISSING")
else:
    print(
        "DEV PREDICT_BATCH:",
        "predict_batch" in dev_adapter["methods"]
    )
    print(
        "NATIVE PREDICT_BATCH:",
        "predict_batch" in native_adapter["methods"]
    )
    print(
        "NATIVE BATCH DISPATCH:",
        "predict_batch" in native_scheduler["source"]
    )
    print(
        "DEV BATCH DISPATCH:",
        "predict_batch" in dev_scheduler["source"]
    )

print("\nSOURCE AUDIT: COMPLETE")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
