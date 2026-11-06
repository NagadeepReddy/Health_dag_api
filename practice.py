
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"
EVIDENCE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence"
FIXTURE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json"

python3 - <<'PY'
from pathlib import Path
import hashlib
import shutil

relative = Path(
    "artifacts/v1.472-max/pzaas_max/"
    "validation/pzaas_forward_schema.json"
)

source = Path.cwd() / relative
target = Path(
    "/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"
) / relative

if not source.is_file():
    raise SystemExit(f"STOP: Original schema missing: {source}")

if not target.parent.is_dir():
    raise SystemExit("STOP: Clean validation directory missing")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if target.exists():
    if digest(source) != digest(target):
        raise SystemExit("STOP: Existing staged schema differs")
    print("CORRECT SCHEMA LOCATION: ALREADY PRESENT")
else:
    shutil.copy2(source, target)
    print("CORRECT SCHEMA LOCATION: RESTORED")

assert digest(source) == digest(target)

print("SCHEMA SHA256: PASS")
print("EXACT RUNTIME PATH:", target)
print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")
PY

test -f "$FIXTURE"
test -f "$EVIDENCE/pzaas_native_response.json"

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$STAGE:/workspace:ro" \
  -v "$EVIDENCE:/evidence:rw" \
  -v "$FIXTURE:/tmp/pzaas_input.json:ro" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import json
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

schema = Path(
    "/workspace/artifacts/v1.472-max/pzaas_max/"
    "validation/pzaas_forward_schema.json"
)

if not schema.is_file():
    raise SystemExit("STOP: Schema unavailable inside clean container")

print("CLEAN RUNTIME SCHEMA: PASS", flush=True)

log = Path("/evidence/pzaas_clean_stage_http.log")
fixture = Path("/tmp/pzaas_input.json")
reference = Path("/evidence/pzaas_native_response.json")

def unpack(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            pass
    return value

def products(payload):
    data = unpack(payload["jsonData"])
    prediction = unpack(data["prediction"])
    result = unpack(prediction["productList"])
    if not isinstance(result, list):
        raise ValueError("Invalid productList")
    return result

print("PZAAS CLEAN MAX SERVE: STARTING", flush=True)

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
            raise RuntimeError("Clean MAX worker exited")
        try:
            with socket.create_connection(
                ("127.0.0.1", 18768), timeout=2
            ):
                break
        except OSError:
            time.sleep(2)
    else:
        raise RuntimeError("Clean MAX startup timeout")

    print("CLEAN MAX HTTP PORT: READY", flush=True)

    request = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=fixture.read_bytes(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(
        request, timeout=180
    ) as response:
        status = response.status
        payload = json.loads(response.read())

    actual = products(payload)
    expected = products(json.loads(reference.read_text()))

    trained = (
        "PZAAS REAL MAX EXECUTION: PASS"
        in log.read_text(errors="replace")
    )

    print("CLEAN HTTP STATUS:", status)
    print("RECOMMENDATION COUNT:", len(actual))
    print("SAVED PRODUCT PARITY:", actual == expected)
    print("TRAINED MAX EXECUTION:", trained)

    if not (
        status == 200
        and len(actual) == 24
        and actual == expected
        and trained
    ):
        raise RuntimeError("Clean-stage acceptance failed")

    Path("/evidence/pzaas_clean_stage_response.json").write_text(
        json.dumps(payload, indent=2)
    )

    print("PZAAS INDEPENDENT CLEAN STAGE: PASS")

except Exception as exc:
    print("CLEAN STAGE BLOCKED:", repr(exc))

    if isinstance(exc, urllib.error.HTTPError):
        print(
            "HTTP ERROR:",
            exc.read(1000).decode(errors="replace")
        )

    lines = log.read_text(errors="replace").splitlines()

    print("=== FIRST ROOT ERROR ===")
    for index, line in enumerate(lines):
        if any(term in line for term in (
            "FileNotFoundError",
            "ModuleNotFoundError",
            "ImportError",
            "KeyError",
            "AttributeError"
        )):
            print("\n".join(lines[max(0,index-3):index+5]))
            break

    print("=== LAST 35 SERVER LOG LINES ===")
    print("\n".join(lines[-35:]))
    raise SystemExit(1)

finally:
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
PY
SH
