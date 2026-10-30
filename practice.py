python3 -B - <<'PY'
from pathlib import Path
import ast

pkg = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2_release_candidate/maxserve_cta_extension"
)

names = [
    "cta_worker_adapter.py",
    "cta_native_scheduler.py",
    "cta_scheduler_factory.py",
    "cta_worker_registration.py",
    "cta_spawn_worker.py",
    "cta_native_launcher.py",
]

trees = {}
for name in names:
    p = pkg / name
    if not p.is_file():
        raise SystemExit("STOP: Missing staged file: " + name)
    trees[name] = ast.parse(p.read_text())

print("STAGED NATIVE SOURCE: PASS")

def default_value(tree, function, parameter):
    for n in ast.walk(tree):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if n.name != function:
            continue
        args = n.args.posonlyargs + n.args.args
        defaults = n.args.defaults
        mapping = dict(zip(
            [a.arg for a in args[len(args)-len(defaults):]],
            defaults
        )) if defaults else {}
        if parameter in mapping:
            return ast.literal_eval(mapping[parameter])
    return None

factory_limit = default_value(
    trees["cta_scheduler_factory.py"],
    "create_cta_scheduler",
    "max_items_per_iteration"
)

scheduler_limit = default_value(
    trees["cta_native_scheduler.py"],
    "__init__",
    "max_items_per_iteration"
)

print("FACTORY BATCH LIMIT:", factory_limit)
print("SCHEDULER BATCH LIMIT:", scheduler_limit)

adapter_methods = {
    n.name
    for n in ast.walk(trees["cta_worker_adapter.py"])
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
}

scheduler_source = (
    pkg / "cta_native_scheduler.py"
).read_text()

print("PREDICT_BATCH:", "predict_batch" in adapter_methods)
print("BATCH DISPATCH:", "batch_fn(" in scheduler_source)

overrides = []
for name in (
    "cta_worker_registration.py",
    "cta_spawn_worker.py",
    "cta_native_launcher.py",
):
    for n in ast.walk(trees[name]):
        if not isinstance(n, ast.Call):
            continue
        for kw in n.keywords:
            if kw.arg == "max_items_per_iteration":
                try:
                    value = ast.literal_eval(kw.value)
                except (ValueError, TypeError):
                    value = "dynamic"
                overrides.append((name, n.lineno, value))

print("WORKER BATCH OVERRIDES:", overrides or "NONE")

ready = (
    factory_limit == 2
    and scheduler_limit == 2
    and "predict_batch" in adapter_methods
    and "batch_fn(" in scheduler_source
    and not any(v == 1 for _, _, v in overrides)
)

print(
    "NATIVE BATCH-2 WIRING:",
    "PASS" if ready else "NEEDS CORRECTION"
)
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
print("LIVE HTTP BATCHING: NOT YET VERIFIED")
PY
