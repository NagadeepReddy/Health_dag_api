
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
from collections import defaultdict
import ast
import hashlib
import json
import os
import shutil
import stat

source = Path("/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106")
target = Path("/application1/sajjna8/PZAAS_MAX_FINAL_CANDIDATE_20261106")

test_rel = Path(
    "model/artifacts/v1.472/core-artifact/bplan/test_samples"
)
pipeline_rel = Path(
    "model/artifacts/v1.472/core-artifact/bplan/pipeline.py"
)

print("=== PZAAS FINAL RELEASE PREPARATION ===")

if not source.is_dir():
    raise SystemExit("STOP: Verified handoff missing")

if target.exists():
    raise SystemExit("STOP: Final candidate already exists")

test_dir = source / test_rel
pipeline_file = source / pipeline_rel

if not test_dir.is_dir() or not pipeline_file.is_file():
    raise SystemExit("STOP: Expected BPLAN files missing")

# Confirm test_samples is referenced only inside __main__.
tree = ast.parse(pipeline_file.read_text())
main_blocks = [
    node for node in tree.body
    if isinstance(node, ast.If)
    and isinstance(node.test, ast.Compare)
    and isinstance(node.test.left, ast.Name)
    and node.test.left.id == "__name__"
    and any(
        isinstance(x, ast.Constant) and x.value == "__main__"
        for x in node.test.comparators
    )
]

if len(main_blocks) != 1:
    raise SystemExit("STOP: BPLAN main guard not uniquely identified")

main_nodes = {id(x) for x in ast.walk(main_blocks[0])}
references = [
    x for x in ast.walk(tree)
    if isinstance(x, ast.Constant)
    and isinstance(x.value, str)
    and "test_samples" in x.value
]

if not references or any(id(x) not in main_nodes for x in references):
    raise SystemExit("STOP: Test samples may be used at runtime")

print("BPLAN TEST REFERENCES: MAIN BLOCK ONLY")

excluded_files = sum(p.is_file() for p in test_dir.rglob("*"))
excluded_bytes = sum(
    p.stat().st_size for p in test_dir.rglob("*") if p.is_file()
)

if shutil.disk_usage(target.parent).free < 5 * 1024**3:
    raise SystemExit("STOP: Insufficient disk space")

def ignore(folder, names):
    result = {
        name for name in names
        if name in {"__pycache__", ".pytest_cache"}
        or name.endswith((".pyc", ".pyo"))
    }
    if Path(folder) == test_dir.parent:
        result.add("test_samples")
    return result

shutil.copytree(source, target, ignore=ignore)
print("REDUCED CANDIDATE: CREATED", flush=True)

required = [
    "model/artifacts/v1.472/core-artifact/pipeline.py",
    "model/artifacts/v1.472/model-settings.json",
    "model/artifacts/v1.472-max/pzaas_max/pzaas_weight_loader.py",
    "model/artifacts/v1.472-max/pzaas_max/validation/pzaas_forward_schema.json",
    "model/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_native_launcher.py",
    "runtime/launch_max_model.sh",
    "config/model.env"
]

for name in required:
    if not (target / name).is_file():
        raise SystemExit("STOP: Required file missing: " + name)

print("REQUIRED RUNTIME FILES: PASS")

# Deduplicate within the new candidate only.
# Preserve both filenames using filesystem hard links.
files = [p for p in target.rglob("*") if p.is_file()]
by_size = defaultdict(list)

for path in files:
    if path.stat().st_size >= 1048576:
        by_size[path.stat().st_size].append(path)

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

groups = []
saved = 0

for candidates in by_size.values():
    if len(candidates) < 2:
        continue

    hashes = defaultdict(list)
    for path in candidates:
        hashes[sha256(path)].append(path)

    for identical in hashes.values():
        if len(identical) < 2:
            continue

        original = identical[0]
        consolidated = [str(original.relative_to(target))]

        for duplicate in identical[1:]:
            if stat.S_IMODE(original.stat().st_mode) != stat.S_IMODE(duplicate.stat().st_mode):
                continue

            temporary = duplicate.with_name(duplicate.name + ".dedup_tmp")
            os.link(original, temporary)
            os.replace(temporary, duplicate)

            if sha256(original) != sha256(duplicate):
                raise SystemExit("STOP: Duplicate verification failed")

            saved += duplicate.stat().st_size
            consolidated.append(str(duplicate.relative_to(target)))

        if len(consolidated) > 1:
            groups.append(consolidated)

manifest = {
    "model": "PZAAS v1.472",
    "status": "Reduced final candidate - generic launcher proof pending",
    "excluded_bplan_test_files": excluded_files,
    "excluded_bytes": excluded_bytes,
    "deduplicated_groups": groups,
    "deduplicated_bytes": saved,
    "previous_packaged_cold_start": "PASS",
    "external_postman": "PASS",
    "generic_launcher_runtime_validation": "PENDING",
    "live_kubernetes_lookup_validation": "PENDING",
    "other_host_portability": "PENDING"
}

report = target / "docs/FINAL_CLEANUP_MANIFEST.json"
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(manifest, indent=2))

print("\n=== FINAL CANDIDATE SUMMARY ===")
print("BPLAN TEST FILES EXCLUDED:", excluded_files)
print("TEST FILE SAVINGS MiB:", round(excluded_bytes / 1048576, 2))
print("DUPLICATE GROUPS CONSOLIDATED:", len(groups))
print("DEDUPLICATION SAVINGS MiB:", round(saved / 1048576, 2))
print("CANDIDATE:", target)
print("REQUIRED RUNTIME: PRESENT")
print("GENERIC LAUNCHER VERIFICATION: NEXT")
print("VERIFIED HANDOFF / DS / CTA / BPLAN: UNCHANGED")
PY
