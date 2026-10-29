python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil
import json

root = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_max"
)
dest = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

required = {
    "build_grecbase_fusion_graph_order_correct",
    "build_real_inputs",
}

found = {}

for p in root.rglob("*.py"):
    if any(x in str(p).lower() for x in (".bak", "backup")):
        continue
    try:
        tree = ast.parse(p.read_text())
    except (SyntaxError, UnicodeError):
        continue

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in required:
                found.setdefault(node.name, []).append(p)

for name in required:
    assert len(found.get(name, [])) == 1, (
        f"STOP: Expected one definition of {name}; "
        f"found {found.get(name, [])}"
    )

assert not dest.exists(), "STOP: Development directory already exists"

sources = set()
for paths in found.values():
    sources.update(paths)

for name in (
    "run_live_max_inference.py",
    "live_cta_pipeline_bridge.py",
):
    p = root / name
    assert p.is_file(), f"STOP: Missing {p}"
    sources.add(p)

dest.mkdir()

for source in sorted(sources):
    relative = source.relative_to(root)
    target = dest / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    assert source.read_bytes() == target.read_bytes()
    print("STAGED:", relative)

manifest = {
    "purpose": "Isolated true MAX batch-2 development",
    "status": "NOT IMPLEMENTED OR VALIDATED",
    "graph_builder": str(found[
        "build_grecbase_fusion_graph_order_correct"
    ][0].relative_to(root)),
    "input_builder": str(found[
        "build_real_inputs"
    ][0].relative_to(root)),
    "required_work": [
        "Parameterize leading batch dimensions",
        "Prepare two independent real input sets",
        "Execute one MAX graph call for both samples",
        "Split two outputs by sample",
        "Verify exact per-request business parity",
        "Integrate scheduler only after passing"
    ]
}

(dest / "batch2_manifest.json").write_text(
    json.dumps(manifest, indent=2)
)

print("\nBATCH-2 DEVELOPMENT COPY: CREATED")
print("DIRECTORY:", dest)
print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
print("TRUE BATCHING: NOT YET VERIFIED")
PY
