
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"
EVIDENCE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence"
FIXTURE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json"

for path in "$STAGE" "$EVIDENCE/pzaas_native_response.json" "$FIXTURE"; do
  test -e "$path" || { echo "STOP: Missing $path"; exit 1; }
done

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

log = Path("/evidence/pzaas_clean_stage_http.log")
fixture = Path("/tmp/pzaas_input.json")
reference = Path("/evidence/pzaas_native_response.json")
output = Path("/evidence/pzaas_clean_stage_response.json")

def unpack(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            pass
    return value

def products(response):
    data = unpack(response["jsonData"])
    prediction = unpack(data["prediction"])
    result = unpack(prediction["productList"])
    if not isinstance(result, list):
        raise ValueError("productList must be a list")
    return result

print("PZAAS CLEAN MAX HTTP: STARTING", flush=True)

with log.open("w") as stream:
    server = subprocess.Popen(
        [
            sys.executable, "-u", "-m",
            "pzaas_native_serve_dev.pzaas_native_launcher"
        ],
        stdout=stream,
        stderr=subprocess.STDOUT
    )

try:
    deadline = time.monotonic() + 150

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Clean MAX worker/server exited")
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
        actual_response = json.loads(response.read())

    actual = products(actual_response)
    expected = products(json.loads(reference.read_text()))

    server_log = log.read_text(errors="replace")
    trained = "PZAAS REAL MAX EXECUTION: PASS" in server_log

    print("HTTP STATUS:", status)
    print("PRODUCT COUNT:", len(actual))
    print("PRODUCT PARITY:", actual == expected)
    print("TRAINED MAX EXECUTION:", trained)

    if not (
        status == 200
        and len(actual) == 24
        and actual == expected
        and trained
    ):
        raise RuntimeError("Clean-stage acceptance failed")

    output.write_text(json.dumps(actual_response, indent=2))
    print("PZAAS INDEPENDENT CLEAN STAGE: PASS")
    print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")

except Exception as exc:
    print("CLEAN STAGE BLOCKED:", repr(exc))
    if isinstance(exc, urllib.error.HTTPError):
        print("HTTP ERROR:", exc.read(1000).decode(errors="replace"))

    lines = log.read_text(errors="replace").splitlines()
    print("=== FIRST ERROR CONTEXT ===")
    error_positions = [
        i for i, line in enumerate(lines)
        if any(x in line for x in (
            "Traceback", "ModuleNotFoundError",
            "FileNotFoundError", "ImportError",
            "KeyError", "RuntimeError"
        ))
    ]
    if error_positions:
        first = error_positions[0]
        print("\n".join(lines[first:first+35]))

    print("=== LAST 45 SERVER LOG LINES ===")
    print("\n".join(lines[-45:]))
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
