cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import os
import shutil
import stat

source = Path(
    "/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106"
)
target = Path(
    "/application1/sajjna8/PZAAS_MAX_FINAL_CANDIDATE_20261106"
)

if not source.is_dir():
    raise SystemExit("STOP: Verified clean handoff missing")

if target.exists():
    raise SystemExit("STOP: Final candidate already exists")

test_rel = Path(
    "model/artifacts/v1.472/core-artifact/bplan/test_samples"
)
test_dir = source / test_rel

print("=== PZAAS SAFE RELEASE REDUCTION ===", flush=True)

# Do not exclude test data if deployed Python code references it.
references = []

if test_dir.is_dir():
    for path in source.rglob("*.py"):
        if test_dir in path.parents:
            continue
        if "test_samples" in path.read_text(errors="replace"):
            references.append(str(path.relative_to(source)))

if references:
    print("TEST SAMPLE REFERENCES:")
    for item in references[:20]:
        print(item)
    raise SystemExit(
        "STOP: Runtime source references test samples. "
        "No candidate created."
    )

excluded_files = (
    sum(p.is_file() for p in test_dir.rglob("*"))
    if test_dir.is_dir() else 0
)

print("BPLAN TEST SAMPLE FILES TO EXCLUDE:", excluded_files)

if shutil.disk_usage(target.parent).free < 5 * 1024**3:
    raise SystemExit("STOP: Insufficient available storage")

def ignore(directory, names):
    excluded = {
        name for name in names
        if name in {"__pycache__", ".pytest_cache"}
        or name.endswith((".pyc", ".pyo"))
    }

    if Path(directory) == test_dir.parent:
        excluded.add("test_samples")

    return excluded

shutil.copytree(source, target, ignore=ignore)

print("FINAL CANDIDATE: COPIED", flush=True)

required = [
    "model/artifacts/v1.472/core-artifact/pipeline.py",
    "model/artifacts/v1.472/model-settings.json",
    "model/artifacts/v1.472-max/pzaas_max/pzaas_weight_loader.py",
    "model/artifacts/v1.472-max/pzaas_max/validation/pzaas_forward_schema.json",
    "model/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_native_launcher.py",
    "runtime/launch_max_model.sh",
    "config/model.env"
]

for item in required:
    if not (target / item).is_file():
        raise SystemExit("STOP: Missing required file: " + item)

print("REQUIRED RUNTIME FILES: PRESENT")

# Consolidate identical contents inside the NEW candidate only.
# Keep both original filenames and paths for runtime compatibility.
files = sorted(p for p in target.rglob("*") if p.is_file())

by_size = defaultdict(list)

for path in files:
    if path.stat().st_size >= 1048576:
        by_size[path.stat().st_size].append(path)

groups = []
saved_bytes = 0

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

for same_size in by_size.values():
    if len(same_size) < 2:
        continue

    by_hash = defaultdict(list)

    for path in same_size:
        by_hash[digest(path)].append(path)

    for identical in by_hash.values():
        if len(identical) < 2:
            continue

        original = identical[0]
        consolidated = [original]

        for duplicate in identical[1:]:
            if (
                stat.S_IMODE(duplicate.stat().st_mode)
                != stat.S_IMODE(original.stat().st_mode)
            ):
                continue

            temporary = duplicate.with_name(
                duplicate.name + ".dedup_tmp"
            )

            os.link(original, temporary)
            os.replace(temporary, duplicate)

            saved_bytes += duplicate.stat().st_size
            consolidated.append(duplicate)

        if len(consolidated) > 1:
            groups.append([
                str(p.relative_to(target))
                for p in consolidated
            ])

print("IDENTICAL CONTENT GROUPS CONSOLIDATED:", len(groups))
print(
    "DUPLICATE STORAGE SAVINGS MiB:",
    round(saved_bytes / 1048576, 1)
)

# Verify that duplicate paths still exist.
for group in groups:
    for relative in group:
        if not (target / relative).is_file():
            raise SystemExit("STOP: Duplicate path lost")

all_files = [
    p for p in target.rglob("*") if p.is_file()
]

logical_size = sum(p.stat().st_size for p in all_files)

manifest = {
    "model": "PZAAS v1.472",
    "status": "final candidate; launcher proof pending",
    "source_handoff": str(source),
    "candidate": str(target),
    "excluded_test_sample_files": excluded_files,
    "consolidated_duplicate_groups": groups,
    "deduplicated_bytes": saved_bytes,
    "file_count": len(all_files),
    "logical_size_bytes": logical_size,
    "original_ds_modified": False,
    "live_kubernetes_lookups": "pending",
    "other_vm_validation": "pending"
}

report = target / "docs/FINAL_CLEANUP_MANIFEST.json"
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(manifest, indent=2))

print("\n=== FINAL CANDIDATE SUMMARY ===")
print("REQUIRED RUNTIME FILES: PASS")
print("TEST SAMPLES EXCLUDED:", excluded_files)
print("DUPLICATE PATHS: PRESERVED")
print("TOTAL FILES:", len(all_files))
print("LOGICAL SIZE GiB:", round(logical_size / 1024**3, 2))
print("CANDIDATE:", target)
print("EXISTING VERIFIED HANDOFF: UNCHANGED")
print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")
print("NEXT: GENERIC LAUNCHER VERIFICATION")
PY
