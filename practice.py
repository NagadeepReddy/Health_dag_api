python3 - <<'PY'
from pathlib import Path
import ast
import shutil

root = Path("/application1")
repo = root / "sajjna8/rt-pzaas-cta-offers-v1"
dev = root / "CTA_MAX_TRUE_BATCH2_DEV_20261029"

working = repo / "artifacts/v1.168-max/maxserve_cta_extension"
source = dev / "native_batch2"
stage = dev / "native_batch2_live_stage"
temporary = dev / "native_batch2_live_stage_build"

names = [
    "cta_worker_adapter.py",
    "cta_native_scheduler.py",
    "cta_scheduler_factory.py",
]

assert working.is_dir()
assert source.is_dir()
assert not stage.exists(), "STOP: Stage already exists"
assert not temporary.exists(), "STOP: Temporary stage exists"

for name in names:
    assert (source / name).is_file()
    ast.parse((source / name).read_text())

def methods(path, class_name):
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                n.name for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return set()

assert {"__init__", "initialize", "predict"} <= methods(
    working / "cta_worker_adapter.py",
    "CTAWorkerAdapter"
)

assert {"__init__", "initialize", "predict", "predict_batch"} <= methods(
    source / "cta_worker_adapter.py",
    "CTAWorkerAdapter"
)

factory = (source / "cta_scheduler_factory.py").read_text()
assert factory.count("max_items_per_iteration=1") == 1

spawn = (working / "cta_spawn_worker.py").read_text()
assert "import CTAWorkerAdapter" in spawn
assert "cta_adapter" in spawn

shutil.copytree(working, temporary, symlinks=True)

for name in names:
    shutil.copy2(source / name, temporary / name)

factory_file = temporary / "cta_scheduler_factory.py"
factory_file.write_text(
    factory.replace(
        "max_items_per_iteration=1",
        "max_items_per_iteration=2",
        1
    )
)

for name in names:
    ast.parse((temporary / name).read_text())

assert "max_items_per_iteration=2" in factory_file.read_text()

temporary.rename(stage)

print("NATIVE BATCH-2 STAGING: PASS")
print("ADAPTER CLASS: CTAWorkerAdapter")
print("BATCH METHOD: predict_batch")
print("BATCH CAPACITY: 2")
print("SYNTAX: PASS")
print("STAGE:", stage)
print("ORIGINAL DS: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("LIVE SERVER: NOT STARTED")
PY
