
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import ast
import hashlib
import json
import re
import shutil
import subprocess
import tarfile

base = Path("/application1/sajjna8")
source = base / "max_shared_infra"
release = base / "MAX_SHARED_INFRA_CLEAN_HANDOFF_20261106"
archive = base / "MAX_SHARED_INFRA_CLEAN_HANDOFF_20261106.tar.gz"
checksum = base / "MAX_SHARED_INFRA_CLEAN_HANDOFF_20261106.tar.gz.sha256"

print("=== CLEAN SHARED MAX INFRASTRUCTURE RELEASE ===")

if any(p.exists() for p in (release, archive, checksum)):
    raise SystemExit("STOP: Existing release detected; nothing overwritten")

required = [
    "bin/run_max_model.sh",
    "bin/run_max_model_shared.sh",
    "python/max_runtime_shared/__init__.py",
    "python/max_runtime_shared/typed_queue.py",
    "python/max_runtime_shared/scheduler_hooks.py",
    "python/max_runtime_shared/router_contract.py",
    "python/max_runtime_shared/worker_lifecycle.py",
]

tests = sorted((source / "tests").glob("test_*.py"))
files = [Path(p) for p in required]
files.extend(p.relative_to(source) for p in tests)

if not tests:
    raise SystemExit("STOP: Shared module tests missing")

# Check the exact clean candidate before creating anything.
for relative in files:
    path = source / relative

    if not path.is_file() or path.is_symlink():
        raise SystemExit(f"STOP: Missing or unsafe file: {relative}")

    content = path.read_text(errors="replace")

    if re.search(r"\b(pzaas|bplan|cta)\b", content, re.I):
        raise SystemExit(
            f"STOP: Model-specific content requires review: {relative}"
        )

    if path.suffix == ".py":
        ast.parse(content, filename=str(path))
    elif path.suffix == ".sh":
        subprocess.run(["bash", "-n", str(path)], check=True)

print("RUNTIME FILE SELECTION: PASS")
print("MODEL-SPECIFIC SOURCE CHECK: PASS")
print("PYTHON AND SHELL SYNTAX: PASS")

release.mkdir()

for relative in files:
    destination = release / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / relative, destination)

readme = """# Shared Modular MAX Infrastructure

## Purpose
Reusable, model-independent runtime infrastructure for native MAX Serve.

## Components
- Generic model launcher
- Optional shared-Python launcher
- Typed response queue
- Scheduler registration hooks
- Route registration contract
- Worker lifecycle contract

## Model requirements
A model supplies its own:
- Pipeline and architecture registration
- Trained weights and inference adapter
- Preprocessing and postprocessing
- JSON request and response contract
- Model-specific scheduler and worker bindings
- Runtime dependencies and model.env configuration

## Usage
bash bin/run_max_model_shared.sh check /path/to/MODEL_PACKAGE

bash bin/run_max_model_shared.sh start /path/to/MODEL_PACKAGE

## Important
Requires an available compatible Modular MAX container image.

The source MAX runtime image is not included.
The model package is not included.
Original model code and handoffs are not included.

## Verification scope
The shared typed queue was validated during PZAAS HTTP 200
and trained MAX inference on the development VM.

The scheduler, router and lifecycle components passed isolated
tests and MAX runtime compatibility checks. They have not yet
all been adopted by the existing model-serving implementations.

Other-machine portability and an approved production image
remain unverified.

Do not replace existing model-specific implementations without
independent integration and regression validation.
"""

(release / "README.md").write_text(readme)

manifest = {
    "release": release.name,
    "type": "model-independent MAX infrastructure",
    "model_files_included": False,
    "trained_weights_included": False,
    "container_image_included": False,
    "verified_live_shared_component": "typed_queue",
    "remaining_model_adoption": [
        "scheduler_hooks",
        "router_contract",
        "worker_lifecycle"
    ],
    "files": {}
}

for path in sorted(release.rglob("*")):
    if path.is_file():
        relative = path.relative_to(release).as_posix()
        manifest["files"][relative] = {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
        }

(release / "MANIFEST.json").write_text(
    json.dumps(manifest, indent=2) + "\n"
)

with tarfile.open(archive, "w:gz") as tar:
    tar.add(release, arcname=release.name)

digest = hashlib.sha256(archive.read_bytes()).hexdigest()
checksum.write_text(f"{digest}  {archive.name}\n")

# Verify archive contents against the clean directory.
with tarfile.open(archive, "r:gz") as tar:
    members = tar.getmembers()

    if any(
        m.issym() or m.islnk() or m.name.startswith("/")
        or ".." in Path(m.name).parts
        for m in members
    ):
        raise SystemExit("STOP: Unsafe archive entry detected")

    actual = sorted(
        m.name.removeprefix(release.name + "/")
        for m in members
        if m.isfile()
    )
    expected = sorted(
        p.relative_to(release).as_posix()
        for p in release.rglob("*")
        if p.is_file()
    )

    if actual != expected:
        raise SystemExit("STOP: Archive manifest mismatch")

print("\n=== RESULT ===")
print("CLEAN SHARED INFRASTRUCTURE PACKAGE: CREATED")
print("ARCHIVE CONTENTS: VERIFIED")
print("SOURCE AND MODEL CODE: UNCHANGED")
print("TRAINED WEIGHTS INCLUDED: NONE")
print("CONTAINER IMAGE INCLUDED: NONE")
print("ORIGINAL HANDOFFS: UNCHANGED")
print("RUNNING CONTAINERS: UNCHANGED")
print("RELEASE:", release)
print("ARCHIVE:", archive)
print("SHA256:", digest)
print("NEXT: INDEPENDENT RELEASE PORTABILITY VALIDATION")
PY
