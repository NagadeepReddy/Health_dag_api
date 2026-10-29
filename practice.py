python3 - <<'PY'
from pathlib import Path
import ast
import shutil

root = Path("/application1")
repo = root / "sajjna8/rt-pzaas-cta-offers-v1"
dev = root / "CTA_MAX_TRUE_BATCH2_DEV_20261029"

working = (
    repo / "artifacts/v1.168-max/maxserve_cta_extension"
)
source = dev / "native_batch2"
stage = dev / "native_batch2_live_stage"

names = (
    "cta_worker_adapter.py",
    "cta_native_scheduler.py",
    "cta_scheduler_factory.py",
)

assert working.is_dir(), "STOP: Native release missing"
assert source.is_dir(), "STOP: Development files missing"
assert not stage.exists(), "STOP: Stage already exists"

for name in names:
    assert (source / name).is_file(), f"STOP: Missing {name}"
    ast.parse((source / name).read_text())

def classes(path):
    tree = ast.parse(path.read_text())
    return {
        n.name: {
            m.name for m in n.body
            if isinstance(m, ast.FunctionDef)
        }
        for n in tree.body
        if isinstance(n, ast.ClassDef)
    }

dev_classes = classes(source / "cta_worker_adapter.py")
assert "CTAWorkerAdapter" in dev_classes
assert {"__init__", "predict", "predict_batch"} <= (
    dev_classes["CTAWorkerAdapter"]
)

working_classes = classes(working / "cta_worker_adapter.py")
assert "CTAMaxWorkerAdapter" in working_classes, (
    "STOP: Working adapter API differs"
)

factory = (source / "cta_scheduler_factory.py").read_text()
assert factory.count("max_items_per_iteration=1") == 1, (
    "STOP: Unexpected batch-capacity configuration"
)

# Create an isolated stage. Never overwrite native release.
shutil.copytree(working, stage, symlinks=True)

for name in names:
    shutil.copy2(source / name, stage / name)

adapter = stage / "cta_worker_adapter.py"
adapter.write_text(
    adapter.read_text()
    + "\nCTAMaxWorkerAdapter = CTAWorkerAdapter\n"
)

factory_file = stage / "cta_scheduler_factory.py"
factory_file.write_text(
    factory.replace(
        "max_items_per_iteration=1",
        "max_items_per_iteration=2",
        1
    )
)

for name in names:
    ast.parse((stage / name).read_text())

print("NATIVE BATCH-2 STAGING: PASS")
print("ADAPTER COMPATIBILITY ALIAS: INSTALLED")
print("BATCH CAPACITY: 2")
print("SYNTAX: PASS")
print("STAGE:", stage)
print("ORIGINAL DS: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("LIVE SERVER: NOT STARTED")
PY
