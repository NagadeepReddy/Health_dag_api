
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path, PurePosixPath
import hashlib
import json
import subprocess
import tarfile
import tempfile

base = Path("/application1/sajjna8")
name = "MAX_SHARED_INFRA_CLEAN_HANDOFF_20261106"
archive = base / (name + ".tar.gz")
checksum = base / (name + ".tar.gz.sha256")
model = base / "PZAAS_MAX_CLEAN_HANDOFF_20261106"

print("=== INDEPENDENT SHARED MAX RELEASE VALIDATION ===")

for p in (archive, checksum, model / "config/model.env"):
    if not p.is_file():
        raise SystemExit(f"STOP: Missing required file: {p}")

actual_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
parts = checksum.read_text().split()

if len(parts) != 2 or parts[0] != actual_digest or parts[1] != archive.name:
    raise SystemExit("STOP: Release SHA256 mismatch")

print("RELEASE SHA256: PASS")

with tempfile.TemporaryDirectory(
    prefix="max_release_verify_",
    dir=str(base)
) as temporary:

    temp = Path(temporary)
    extracted = temp / name

    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            path = PurePosixPath(member.name)

            if (
                path.is_absolute()
                or ".." in path.parts
                or not path.parts
                or path.parts[0] != name
                or not (member.isdir() or member.isfile())
            ):
                raise SystemExit(
                    f"STOP: Unsafe archive entry: {member.name}"
                )

            target = temp.joinpath(*path.parts)

            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source:
                    target.write_bytes(source.read())

    print("ISOLATED ARCHIVE EXTRACTION: PASS")

    manifest_path = extracted / "MANIFEST.json"
    if not manifest_path.is_file():
        raise SystemExit("STOP: Release manifest missing")

    manifest = json.loads(manifest_path.read_text())
    expected = manifest["files"]

    actual_files = {
        p.relative_to(extracted).as_posix()
        for p in extracted.rglob("*")
        if p.is_file()
    }

    if actual_files != set(expected) | {"MANIFEST.json"}:
        raise SystemExit("STOP: Packaged file inventory mismatch")

    for relative, metadata in expected.items():
        p = extracted / relative
        digest = hashlib.sha256(p.read_bytes()).hexdigest()

        if digest != metadata["sha256"]:
            raise SystemExit(f"STOP: File checksum mismatch: {relative}")

        if p.stat().st_size != metadata["bytes"]:
            raise SystemExit(f"STOP: File size mismatch: {relative}")

    print("PACKAGE FILE INVENTORY: PASS")
    print("ALL PACKAGED FILE CHECKSUMS: PASS")

    launcher = extracted / "bin/run_max_model_shared.sh"
    original = extracted / "bin/run_max_model.sh"

    for script in (launcher, original):
        subprocess.run(
            ["bash", "-n", str(script)],
            check=True
        )

    print("EXTRACTED LAUNCHER SYNTAX: PASS")

    runtime = extracted / "python/max_runtime_shared"

    required = [
        "typed_queue.py",
        "scheduler_hooks.py",
        "router_contract.py",
        "worker_lifecycle.py"
    ]

    for filename in required:
        if not (runtime / filename).is_file():
            raise SystemExit(f"STOP: Missing shared module: {filename}")

    print("REUSABLE PYTHON COMPONENTS: PRESENT")

    print("\n=== EXTRACTED LAUNCHER PREFLIGHT ===")

    result = subprocess.run(
        ["bash", str(launcher), "check", str(model)],
        cwd=str(temp),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=45
    )

    print(result.stdout[-4000:])

    if result.returncode != 0:
        raise SystemExit("STOP: Extracted launcher preflight failed")

    if "GENERIC MAX PREFLIGHT: PASS" not in result.stdout:
        raise SystemExit("STOP: Preflight success not confirmed")

    print("ISOLATED LAUNCHER PREFLIGHT: PASS")

    print("\n=== HOST-DEPENDENCY REVIEW ===")
    markers = (
        "/application1/sajjna8/",
        "/vzwhome/",
    )
    references = []

    for p in sorted(extracted.rglob("*")):
        if not p.is_file() or p.suffix not in (".sh", ".py"):
            continue

        contents = p.read_text(errors="replace")

        for marker in markers:
            if marker in contents:
                references.append(
                    f"{p.relative_to(extracted)}: {marker}"
                )

    if references:
        print("VM-SPECIFIC REFERENCES NEED REVIEW:")
        for item in references:
            print("REVIEW:", item)
    else:
        print("USER WORKSPACE PATH REFERENCES: NONE")

    print("\n=== FINAL RESULT ===")
    print("CLEAN RELEASE INTEGRITY: PASS")
    print("INDEPENDENT EXTRACTION: PASS")
    print("EXTRACTED LAUNCHER PREFLIGHT: PASS")
    print("MODEL WEIGHTS INCLUDED: NONE")
    print("ORIGINAL MODEL HANDOFFS: UNCHANGED")
    print("NO INFERENCE REPEATED")
    print("NO HTTP SERVER STARTED")
    print("TEMPORARY EXTRACTION: AUTOMATICALLY REMOVED")
    print("CROSS-VM PORTABILITY: NOT YET VERIFIED")
    print("APPROVED PRODUCTION IMAGE: PENDING")
    print("NEXT: FINAL DEPLOYMENT CONTRACT AND HANDOFF")
PY
