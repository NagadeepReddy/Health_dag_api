
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

export PZAAS_REPO="$PWD"
export PZAAS_STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"
export PZAAS_EVIDENCE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence"
export PZAAS_FIXTURE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json"

python3 - <<'PY'
from pathlib import Path
import json
import os
import shutil

repo = Path(os.environ["PZAAS_REPO"])
stage = Path(os.environ["PZAAS_STAGE"])

if stage.exists():
    raise SystemExit(f"STOP: Stage already exists: {stage}")

if shutil.disk_usage(stage.parent).free < 8 * 1024**3:
    raise SystemExit("STOP: Insufficient staging disk space")

sources = {
    "original_ds": (
        repo / "artifacts/v1.472",
        Path("artifacts/v1.472")
    ),
    "max_graph": (
        repo / "artifacts/v1.472-max/pzaas_max",
        Path("artifacts/v1.472-max/pzaas_max")
    ),
    "native_serve": (
        repo / "artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev",
        Path("artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev")
    ),
}

for name, (source, _) in sources.items():
    if not source.is_dir():
        raise SystemExit(f"STOP: Missing {name}: {source}")

exclude_dirs = {
    "__pycache__", ".pytest_cache", ".git",
    "tests", "test", "samples", "benchmarks",
    "logs", ".venv", "venv"
}

def include(scope, relative):
    parts = relative.parts
    name = relative.name.lower()

    if any(part.lower() in exclude_dirs for part in parts):
        return False

    if name.endswith((
        ".pyc", ".pyo", ".log", ".bak", ".tmp",
        ".tar", ".tar.gz", ".zip", ".before_pack72"
    )):
        return False

    if scope == "max_graph" and parts[0] == "validation":
        return relative.as_posix() in {
            "validation/__init__.py",
            "validation/pzaas_forward_input_adapter.py"
        }

    if scope == "native_serve":
        return (
            relative.suffix.lower() in {
                ".py", ".npy", ".npz", ".json"
            }
            and "adjusted_sanity" not in name
            and not name.startswith("test_")
        )

    return True

manifest = []
stage.mkdir(parents=True)

for scope, (source, destination) in sources.items():
    count = 0
    total = 0

    for file in sorted(source.rglob("*")):
        if not file.is_file():
            continue

        relative = file.relative_to(source)
        if not include(scope, relative):
            continue

        target = stage / destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)

        size = target.stat().st_size
        count += 1
        total += size

        manifest.append({
            "scope": scope,
            "path": str(target.relative_to(stage)),
            "size_bytes": size
        })

    print(
        f"{scope}: {count} files, "
        f"{total / 1048576:.1f} MiB",
        flush=True
    )

# Preserve package structure where present.
extension_source = (
    repo / "artifacts/v1.472-max/maxserve_pzaas_extension/__init__.py"
)
if extension_source.is_file():
    destination = (
        stage / "artifacts/v1.472-max/"
        "maxserve_pzaas_extension/__init__.py"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(extension_source, destination)
    manifest.append({
        "scope": "package",
        "path": str(destination.relative_to(stage)),
        "size_bytes": destination.stat().st_size
    })

required = (
    "artifacts/v1.472/model-settings.json",
    "artifacts/v1.472/core-artifact/pipeline.py",
    "artifacts/v1.472-max/pzaas_max/pzaas_weight_loader.py",
    "artifacts/v1.472-max/pzaas_max/validation/pzaas_forward_input_adapter.py",
    "artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_native_launcher.py",
    "artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_live_pack_72.py"
)

for relative in required:
    if not (stage / relative).is_file():
        raise SystemExit(f"STOP: Required runtime file missing: {relative}")

(stage / "RUNTIME_MANIFEST.json").write_text(
    json.dumps(manifest, indent=2)
)

(stage / "STAGING_NOTES.md").write_text(
    "# PZAAS v1.472 clean staging candidate\n\n"
    "Model-specific DS and MAX integration source.\n\n"
    "Not yet a certified portable or production release.\n"
    "Current development runtime: localhost/cta-max-faiss:local.\n"
    "Python dependencies: /application1/max_shared_python_deps.\n"
    "Runtime import validation and clean HTTP proof required.\n"
    "Live Kubernetes lookups and external Postman remain pending.\n"
    "Model-independent shared MAX infrastructure remains a separate task.\n"
)

print("PZAAS CLEAN STAGE: CREATED")
print("STAGE:", stage)
print("MANIFEST:", stage / "RUNTIME_MANIFEST.json")
print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$PZAAS_STAGE:/workspace:ro" \
  -v "$PZAAS_EVIDENCE:/evidence:rw" \
  -v "$PZAAS_FIXTURE:/tmp/pzaas_adjusted_input.json:ro" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PYTEST'
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

log = Path("/evidence/pzaas_clean_stage_http.log")
fixture = Path("/tmp/pzaas_adjusted_input.json")
reference = Path("/evidence/pzaas_native_response.json")

def unpack(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            pass
    return value

def products(payload):
    body = unpack(payload["jsonData"])
    prediction = unpack(body["prediction"])
    return unpack(prediction["productList"])

print("PZAAS CLEAN STAGE: STARTING", flush=True)

with log.open("w") as output:
    server = subprocess.Popen(
        [
            sys.executable, "-u", "-m",
            "pzaas_native_serve_dev.pzaas_native_launcher"
        ],
        stdout=output,
        stderr=subprocess.STDOUT
    )

try:
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Clean MAX server exited")
        try:
            with socket.create_connection(
                ("127.0.0.1", 18768), timeout=2
            ):
                break
        except OSError:
            time.sleep(2)
    else:
        raise RuntimeError("Clean MAX server startup timeout")

    request = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=fixture.read_bytes(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        status = response.status
        payload = json.loads(response.read())

    print("CLEAN STAGE HTTP STATUS:", status, flush=True)

    actual = products(payload)
    expected = products(json.loads(reference.read_text()))

    print("CLEAN PRODUCT COUNT:", len(actual))
    print("PREVIOUS PRODUCT COUNT:", len(expected))
    print("CLEAN PRODUCT PARITY:", actual == expected)

    execution = (
        "PZAAS REAL MAX EXECUTION: PASS"
        in log.read_text(errors="replace")
    )

    print("CLEAN TRAINED MAX EXECUTION:", execution)

    if not (
        status == 200
        and len(actual) == 24
        and actual == expected
        and execution
    ):
        raise RuntimeError("Clean stage proof did not match working POC")

    print("PZAAS INDEPENDENT CLEAN STAGE: PASS")

except Exception as exc:
    print("PZAAS CLEAN STAGE BLOCKED:", repr(exc))
    print("=== LAST 30 SERVER LOG LINES ===")
    print(
        "\n".join(
            log.read_text(errors="replace").splitlines()[-30:]
        )
    )
    raise SystemExit(1)

finally:
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
PYTEST
SH
