cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"
EVIDENCE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence"
FIXTURE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json"

python3 - <<'PY'
from pathlib import Path
import shutil

source = Path(
    "artifacts/v1.472-max/pzaas_max/"
    "validation/python_deps/joblib"
)

destination = Path(
    "/application1/max_shared_python_deps/joblib"
)

if not (source / "__init__.py").is_file():
    raise SystemExit(
        "STOP: Validated source joblib package not found"
    )

if destination.exists():
    if not (destination / "__init__.py").is_file():
        raise SystemExit(
            "STOP: Existing shared joblib is incomplete"
        )
    print("SHARED JOBLIB: ALREADY PRESENT")
else:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", "*.pyo"
        )
    )
    print("SHARED JOBLIB: INSTALLED")

print("ORIGINAL MODEL / CTA / BPLAN: UNCHANGED")
PY

test -d "$STAGE"
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
import traceback
import urllib.error
import urllib.request
from pathlib import Path

print("=== CLEAN STAGE DEPENDENCY VERIFICATION ===", flush=True)

try:
    import joblib
    from transformers import AutoTokenizer
    from max.serve.scheduler.queues import SchedulerZmqConfigs
except Exception:
    traceback.print_exc()
    raise SystemExit("CLEAN DEPENDENCY IMPORT: FAILED")

print("JOBLIB IMPORT: PASS")
print("MAX / TRANSFORMERS IMPORT: PASS", flush=True)

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
    return unpack(prediction["productList"])

print("=== CLEAN MAX SERVE STARTING ===", flush=True)

with log.open("w") as output:
    server = subprocess.Popen(
        [
            sys.executable,
            "-u",
            "-m",
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
        raise RuntimeError("MAX Serve startup timeout")

    print("CLEAN MAX SERVER: READY", flush=True)

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
        result = json.loads(response.read())

    actual = products(result)
    expected = products(
        json.loads(reference.read_text())
    )

    execution = (
        "PZAAS REAL MAX EXECUTION: PASS"
        in log.read_text(errors="replace")
    )

    print("HTTP STATUS:", status)
    print("RECOMMENDATION COUNT:", len(actual))
    print("SAVED RESPONSE PRODUCT PARITY:", actual == expected)
    print("REAL TRAINED MAX EXECUTION:", execution)

    if (
        status != 200
        or len(actual) != 24
        or actual != expected
        or not execution
    ):
        raise RuntimeError(
            "Clean stage verification did not pass"
        )

    print("PZAAS INDEPENDENT CLEAN STAGE: PASS")

except Exception as exc:
    print("CLEAN STAGE BLOCKED:", repr(exc))

    if isinstance(exc, urllib.error.HTTPError):
        print(
            "HTTP BODY:",
            exc.read(800).decode(errors="replace")
        )

    print("=== LAST 35 SERVER LOG LINES ===")
    print(
        "\n".join(
            log.read_text(errors="replace").splitlines()[-35:]
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
PY
SH
