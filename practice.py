cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil

root = Path("artifacts/v1.168-max")
dst = Path("/application1/cta_max_true_batch_dev_20261028")
src_graphs = root / "cta_max"
src_ext = Path("/application1/cta_max_native_release_candidate_20261028")

assert src_graphs.is_dir(), "STOP: MAX graph source missing"
assert src_ext.is_dir(), "STOP: Validated integration missing"
assert not dst.exists(), "STOP: Batch workspace already exists"
assert shutil.disk_usage("/application1").free > 2 * 1024**3, \
    "STOP: Insufficient disk space"

# Copy Python source only. Do not duplicate model weights or test data.
sources = sorted(src_graphs.rglob("*.py"))
assert sources, "STOP: No MAX Python source found"

for p in sources:
    ast.parse(p.read_text())

for p in src_ext.rglob("*.py"):
    ast.parse(p.read_text())

(dst / "cta_max").mkdir(parents=True)

for p in sources:
    target = dst / "cta_max" / p.relative_to(src_graphs)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)

shutil.copytree(src_ext, dst / "maxserve_cta_extension")

print("TRUE BATCH DEVELOPMENT WORKSPACE: PASS")
print("MAX PYTHON FILES COPIED:", len(sources))
print("VALIDATED EXTENSION: COPIED")
print("SOURCE SYNTAX: PASS")
print("LOCATION:", dst)

print("\n=== LIVE INFERENCE ENTRY POINT ===")
for name in (
    "run_live_max_inference.py",
    "live_cta_pipeline_bridge.py",
):
    p = src_graphs / name
    if p.exists():
        print("\nFILE:", name)
        for number, line in enumerate(p.read_text().splitlines(), 1):
            if any(x in line for x in (
                "import ", "Graph(", "compile(", ".execute(",
                "InferenceSession", "shape",
            )):
                print(f"{number}: {line.strip()[:180]}")

print("\nWORKING HTTP 200 CODE: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MODEL STARTUP: NOT PERFORMED")
PY
