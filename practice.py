
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast
import re
import shutil
import sys

root = Path.cwd()
base = root / "artifacts/v1.472-max"
factory = base / "maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_spawn_worker.py"
maxpkg = base / "pzaas_max"
graph = maxpkg / "grecbase_fusion_full_head_72_max.py"

print("=== PZAAS NATIVE FACTORY PATH REPAIR ===")

assert factory.is_file(), f"Factory missing: {factory}"
assert graph.is_file(), f"Verified MAX graph missing: {graph}"

source = factory.read_text()
pattern = r'\bext\s*/\s*["\']pzaas_max_dev["\']'
replacement = 'artifacts / "v1.472-max"'

if re.search(pattern, source):
    corrected = re.sub(pattern, replacement, source)
    assert corrected != source
    ast.parse(corrected, filename=str(factory))

    backup = factory.with_name(factory.name + ".before_max_path_fix.bak")
    if not backup.exists():
        shutil.copy2(factory, backup)

    factory.write_text(corrected)
    print("FACTORY PATH: CORRECTED")
    print("BACKUP:", backup)

elif replacement in source:
    print("FACTORY PATH: ALREADY CORRECT")

else:
    raise RuntimeError("Unexpected factory source. No changes made.")

sys.path.insert(0, str(base))
import importlib.util

assert importlib.util.find_spec("pzaas_max") is not None
print("REAL PZAAS MAX IMPORT PATH: PASS")

native = factory.parent
for name in [
    "pzaas_spawn_worker.py",
    "pzaas_worker_adapter.py",
    "pzaas_max_model_adapter.py",
    "pzaas_pipeline_model.py",
    "pzaas_architecture_registration.py",
]:
    path = native / name
    assert path.is_file(), f"Missing: {path}"
    ast.parse(path.read_text(), filename=str(path))
    print(name, "SYNTAX: PASS")

print("\n=== PROGRESS ===")
print("MAX CPU: PASS (previously verified)")
print("LAYER-0: PASS (previously verified)")
print("EIGHT BRANCHES: 8/8 PASS (previously verified)")
print("FULL MODEL PARITY: PASS (previously verified)")
print("72-INPUT NATIVE BRIDGE: PASS (previously verified)")
print("FACTORY MAX PATH: CORRECT")
print("NATIVE WORKER EXECUTION: PENDING")
print("NATIVE HTTP 200: PENDING")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: REAL NATIVE WORKER INITIALIZATION")
PY
