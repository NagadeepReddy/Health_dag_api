
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"
EVIDENCE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence"
FIXTURE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json"

test -d "$STAGE"
test -f "$FIXTURE"
test -f "$EVIDENCE/pzaas_native_response.json"

python3 - <<'PY'
from pathlib import Path
import shutil

source_root = Path(
    "artifacts/v1.472-max/pzaas_max/validation/python_deps"
)
shared = Path("/application1/max_shared_python_deps")

sources = [
    source_root / "threadpoolctl.py",
    source_root / "threadpoolctl"
]

source = next((p for p in sources if p.exists()), None)
destination = shared / (source.name if source else "threadpoolctl.py")

if not shared.is_dir():
    raise SystemExit("STOP: Shared dependency directory missing")

if (shared / "threadpoolctl.py").is_file() or (
    shared / "threadpoolctl/__init__.py"
).is_file():
    print("SHARED THREADPOOLCTL: ALREADY PRESENT")

elif source is None:
    raise SystemExit(
        "STOP: Validated threadpoolctl source not found. "
        "No files modified."
    )

elif destination.exists():
    raise SystemExit("STOP: Conflicting shared dependency path")

elif source.is_dir():
    shutil.copytree(
        source, destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
    print("SHARED THREADPOOLCTL: INSTALLED")

else:
    shutil.copy2(source, destination)
    print("SHARED THREADPOOLCTL: INSTALLED")

print("ORIGINAL DS / WEIGHTS / IMAGE: UNCHANGED")
PY

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

print("=== CLEAN RUNTIME DEPENDENCY CHECK ===", flush=True)

try:
    import joblib
    import cloudpickle
    import threadpoolctl
    import sklearn
    from transformers import AutoTokenizer
    from max.serve.scheduler.queues import SchedulerZmqConfigs
except Exception:
    traceback.print_exc()
    raise SystemExit("CLEAN RUNTIME IMPORT: FAILED")

print("JOBLIB / CLOUDPICKLE / THREADPOOLCTL: PASS")
print("SKLEARN VERSION:", sklearn.__version__)
print("TRANSFORMERS / MAX: PASS", flush=True)

log = Path("/evidence/pzaas_clean_stage_http.log")
fixture = Path("/tmp/pzaas_input.json")
reference = Path("/evidence/pzaas_native_response.json")
output_file = Path("/evidence/pzaas_clean_stage_response.json")

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
    result = unpack(prediction["productList"])
    if not isinstance(result, list):
        raise ValueError("productList is not a list")
    return result

print("=== INDEPENDENT CLEAN MAX SERVE ===", flush=True)

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
        raise RuntimeError("Clean MAX startup timeout")

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
        payload = json.loads(response.read())

    actual = products(payload)
    expected = products(json.loads(reference.read_text()))

    trained = (
        "PZAAS REAL MAX EXECUTION: PASS"
        in log.read_text(errors="replace")
    )

    print("CLEAN HTTP STATUS:", status)
    print("PRODUCT COUNT:", len(actual))
    print("PRODUCT PARITY:", actual == expected)
    print("TRAINED MAX EXECUTION:", trained)

    if not (
        status == 200
        and len(actual) == 24
        and actual == expected
        and trained
    ):
        raise RuntimeError("Clean stage acceptance check failed")

    output_file.write_text(json.dumps(payload, indent=2))
    print("PZAAS INDEPENDENT CLEAN STAGE: PASS")
    print("CLEAN EVIDENCE: SAVED")

except Exception as exc:
    print("CLEAN STAGE BLOCKED:", repr(exc))

    if isinstance(exc, urllib.error.HTTPError):
        print(
            "HTTP ERROR:",
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
