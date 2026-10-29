python3 -S -B - <<'PY'
from pathlib import Path
import ast
import shutil
import json

repo = Path.cwd()
assert repo.name == "rt-pzaas-cta-offers-v1", (
    f"STOP: Unexpected working directory: {repo}"
)

root = repo / "artifacts/v1.168-max/cta_max"
dest = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")

runner = root / "run_live_max_inference.py"
bridge = root / "live_cta_pipeline_bridge.py"

assert runner.is_file(), f"STOP: Missing {runner}"
assert bridge.is_file(), f"STOP: Missing {bridge}"
assert not dest.exists(), "STOP: Development directory already exists"

tree = ast.parse(runner.read_text())

required = (
    "build_grecbase_fusion_graph_order_correct",
    "build_real_inputs",
)

sources = {runner, bridge}

for function in required:
    modules = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and any(alias.name == function for alias in node.names)
    ]

    assert len(modules) == 1 and modules[0], (
        f"STOP: Cannot uniquely resolve import for {function}: {modules}"
    )

    filename = modules[0].split(".")[-1] + ".py"
    source = root / filename

    assert source.is_file(), f"STOP: Imported source missing: {source}"

    source_tree = ast.parse(source.read_text())
    assert any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function
        for node in source_tree.body
    ), f"STOP: Function not defined in {source}"

    sources.add(source)
    print("RESOLVED:", function, "->", source.name)

for source in sources:
    ast.parse(source.read_text())

dest.mkdir()

for source in sorted(sources):
    target = dest / source.name
    shutil.copy2(source, target)
    assert target.read_bytes() == source.read_bytes()
    print("STAGED:", source.name)

manifest = {
    "purpose": "Isolated MAX true batch-2 prototype",
    "status": "NOT IMPLEMENTED OR TESTED",
    "sources": sorted(p.name for p in sources),
    "working_native_release": "unchanged",
    "original_ds_code": "unchanged",
}

(dest / "batch2_manifest.json").write_text(
    json.dumps(manifest, indent=2)
)

print("\nBATCH-2 DEVELOPMENT COPY: CREATED")
print("DIRECTORY:", dest)
print("SOURCE VALIDATION: PASS")
print("WORKING RELEASE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
