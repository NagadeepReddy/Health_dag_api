
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import shutil
import tarfile
import tempfile

base = Path("/application1/sajjna8")
old = "MAX_SHARED_INFRA_CLEAN_HANDOFF_20261106"
new = "MAX_SHARED_INFRA_TEAM_HANDOFF_20261106"

source = base / (old + ".tar.gz")
source_sha = base / (old + ".tar.gz.sha256")
final_dir = base / new
final_tar = base / (new + ".tar.gz")
final_sha = base / (new + ".tar.gz.sha256")

print("=== FINAL SHARED MAX POC HANDOFF ===")

if any(p.exists() for p in (final_dir, final_tar, final_sha)):
    raise SystemExit("STOP: Team handoff already exists")

if not source.is_file() or not source_sha.is_file():
    raise SystemExit("STOP: Verified source archive missing")

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

recorded = source_sha.read_text().split()
if (
    len(recorded) != 2
    or recorded[0] != digest(source)
    or recorded[1] != source.name
):
    raise SystemExit("STOP: Source archive SHA256 mismatch")

contract = """# Shared Modular MAX Infrastructure — Deployment Contract

## Release classification
Reusable CPU MAX Serve infrastructure — validated POC.
NOT a production-approved deployment.

## Architecture
Three separate deliverables:
1. Shared infrastructure: launchers, typed queue, scheduler hooks,
   router contract, and worker lifecycle.
2. Model-specific package: graph, weights, native serving adapter,
   request/response contract, and original DS implementation.
3. Compatible Modular MAX container image.

Model code must not be copied into shared infrastructure.

## Required model package layout
MODEL_PACKAGE/
  model/
  runtime/python_deps/
  config/model.env

The model provides its own native MAX Serve entrypoint and
configuration accepted by the generic launcher.

## Deployment commands
From the extracted shared infrastructure folder:

  bash bin/run_max_model_shared.sh check /path/to/MODEL_PACKAGE

  bash bin/run_max_model_shared.sh start /path/to/MODEL_PACKAGE

Use a free host port and a compatible locally available MAX image.
Review the model package's config/model.env before starting.

## Runtime requirements
- Linux host with Podman and sufficient CPU/RAM/storage.
- Compatible Modular MAX image loaded on that host.
- Model-specific runtime dependencies available.
- Host and internal ports configured without conflicts.
- External Kubernetes services reachable if the model requires them.

The current development image alias is:
  localhost/max-shared-runtime:cpu

This alias is NOT confirmation of an approved production image.

## Verified on November 6, 2026
- Shared Python module unit tests passed.
- Actual installed MAX API compatibility passed.
- Generic shared launcher served the existing PZAAS package.
- Isolated shared typed-queue overlay served HTTP 200.
- Response contained 24 recommendations.
- Trained MAX inference execution was confirmed.
- Clean archive integrity and isolated extraction passed.
- Extracted launcher preflight passed on the development VM.

## Important limitations
- Shared typed queue: live PZAAS HTTP integration verified.
- Shared scheduler hooks: isolated testing completed;
  live model adoption is not yet verified.
- Shared router contract: isolated testing completed;
  live model adoption is not yet verified.
- Shared worker lifecycle: isolated testing completed;
  live model adoption is not yet verified.
- Other-host / cross-VM portability is not verified.
- Production image approval is pending.
- Live Kubernetes lookup connectivity is not verified.
- GPU and batch-2 production serving are not certified.

## Model migration process
1. Identify the model architecture and dependencies.
2. Preserve original DS model, preprocessing, postprocessing,
   business logic, and JSON contract.
3. Implement an isolated model-specific MAX inference adapter.
4. Supply a compatible model package and model.env.
5. Validate numerical and business parity.
6. Validate native MAX Serve HTTP using real JSON.
7. Integrate shared hooks without duplicate registrations.
8. Verify independent deployment and capture evidence.

## Protection
The verified CTA, BPLAN and PZAAS handoffs are separate.
Do not modify them to deploy this infrastructure.

## Release acceptance
Approved as a reusable infrastructure POC handoff.
Production approval requires separate environment validation.
"""

with tempfile.TemporaryDirectory(
    prefix="max_handoff_build_", dir=str(base)
) as temporary:
    temp = Path(temporary)
    stage = temp / new
    stage.mkdir()

    with tarfile.open(source, "r:gz") as tar:
        seen = set()

        for member in tar.getmembers():
            name = PurePosixPath(member.name)

            if (
                name.is_absolute()
                or ".." in name.parts
                or not name.parts
                or name.parts[0] != old
                or not (member.isfile() or member.isdir())
            ):
                raise SystemExit("STOP: Unsafe source archive")

            relative = Path(*name.parts[1:])

            if not relative.parts:
                continue

            target = stage / relative

            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue

            if relative in seen:
                raise SystemExit("STOP: Duplicate archive entry")

            seen.add(relative)
            target.parent.mkdir(parents=True, exist_ok=True)

            with tar.extractfile(member) as inp:
                with target.open("wb") as out:
                    shutil.copyfileobj(inp, out)

            os.chmod(target, member.mode & 0o777)

    manifest_path = stage / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())

    for relative, info in manifest["files"].items():
        path = stage / relative

        if (
            not path.is_file()
            or digest(path) != info["sha256"]
            or path.stat().st_size != info["bytes"]
        ):
            raise SystemExit(
                f"STOP: Source manifest mismatch: {relative}"
            )

    (stage / "DEPLOYMENT_CONTRACT.md").write_text(contract)

    manifest["release"] = new
    manifest["classification"] = "Validated POC handoff"
    manifest["production_approved"] = False
    manifest["cross_vm_verified"] = False
    manifest["files"] = {}

    for path in sorted(stage.rglob("*")):
        if path.is_file() and path != manifest_path:
            relative = path.relative_to(stage).as_posix()
            manifest["files"][relative] = {
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }

    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n"
    )

    built_tar = temp / (new + ".tar.gz")

    with tarfile.open(built_tar, "w:gz") as tar:
        tar.add(stage, arcname=new)

    with tarfile.open(built_tar, "r:gz") as tar:
        packaged = {
            m.name.removeprefix(new + "/")
            for m in tar.getmembers()
            if m.isfile()
        }

    expected = {
        p.relative_to(stage).as_posix()
        for p in stage.rglob("*")
        if p.is_file()
    }

    if packaged != expected:
        raise SystemExit("STOP: Team archive inventory mismatch")

    final_digest = digest(built_tar)

    stage.rename(final_dir)
    built_tar.replace(final_tar)
    final_sha.write_text(
        f"{final_digest}  {final_tar.name}\n"
    )

print("\n=== RESULT ===")
print("TEAM HANDOFF: CREATED")
print("DEPLOYMENT CONTRACT: INCLUDED")
print("SOURCE ARCHIVE INTEGRITY: PASS")
print("FINAL ARCHIVE CONTENTS: VERIFIED")
print("FINAL SHA256: CREATED")
print("MODEL-SPECIFIC SOURCE: NOT INCLUDED")
print("TRAINED WEIGHTS: NOT INCLUDED")
print("ORIGINAL HANDOFFS: UNCHANGED")
print("RUNNING CONTAINERS: UNCHANGED")
print("PRODUCTION APPROVAL: PENDING")
print("RELEASE:", final_dir)
print("ARCHIVE:", final_tar)
print("SHA256:", final_digest)
print("NEXT: FINAL TEAM HANDOFF REVIEW")
PY
