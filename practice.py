
python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil
import json

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
dest = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

files = [
    "grecbase_fusion_order_correct_max.py",
    "real_sanity_input_adapter.py",
    "run_live_max_inference.py",
    "live_cta_pipeline_bridge.py",
]

assert root.is_dir(), "STOP: Source directory missing"
assert not dest.exists(), "STOP: Development copy already exists"

for name in files:
    p = root / name
    assert p.is_file(), f"STOP: Missing {p}"
    ast.parse(p.read_text())

dest.mkdir()

for name in files:
    src = root / name
    dst = dest / name
    shutil.copy2(src, dst)
    assert src.read_bytes() == dst.read_bytes()
    print("STAGED:", name)

manifest = {
    "purpose": "Isolated MAX true batch-2 prototype",
    "status": "NOT YET IMPLEMENTED",
    "source_files": files,
    "original_ds_code": "unchanged",
    "working_release": "unchanged",
    "next": "Implement batch-2 graph and input/output handling; validate parity before integration"
}

(dest / "batch2_manifest.json").write_text(
    json.dumps(manifest, indent=2)
)

print("\nBATCH-2 DEVELOPMENT COPY: CREATED")
print("DIRECTORY:", dest)
print("SOURCE SYNTAX: PASS")
print("WORKING RELEASE: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
