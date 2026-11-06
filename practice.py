
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

ORIGINAL="artifacts/v1.472/samples/sanity_input.json"
ADJUSTED="artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json"

export ORIGINAL ADJUSTED

python3 - <<'PY'
import json
import os
from pathlib import Path

source = Path(os.environ["ORIGINAL"])
target = Path(os.environ["ADJUSTED"])

data = json.loads(source.read_text())
fixed = [0]

def adjust(obj):
    if isinstance(obj, dict):
        page = obj.get("page")
        if (
            isinstance(page, dict)
            and str(page.get("name", "")).lower() == "gridwall_smartphones"
            and obj.get("webinteraction_name") is None
        ):
            obj["webinteraction_name"] = ""
            fixed[0] += 1
        for value in obj.values():
            adjust(value)
    elif isinstance(obj, list):
        for value in obj:
            adjust(value)

adjust(data)

print("PZAAS NULL FIELDS CORRECTED:", fixed[0], flush=True)

if fixed[0] == 0:
    raise SystemExit("No matching null fields; original fixture not modified")

target.write_text(json.dumps(data, indent=2))
print("ADJUSTED TEST FIXTURE: SAVED", flush=True)
print("ORIGINAL DS AND INPUT: UNCHANGED", flush=True)
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$PWD:/workspace:ro" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /workspace \
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

fixture = Path(
    "/workspace/artifacts/v1.472-max/"
    "maxserve_pzaas_extension/pzaas_native_serve_dev/"
    "pzaas_adjusted_sanity_input.json"
)

log = Path("/tmp/pzaas_adjusted_http.log")
body = fixture.read_bytes()

print("PZAAS BUILT-IN MAX SERVE: STARTING", flush=True)

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
            raise RuntimeError("MAX Serve exited before HTTP startup")
        try:
            with socket.create_connection(
                ("127.0.0.1", 18768), timeout=2
            ):
                break
        except OSError:
            time.sleep(2)
    else:
        raise RuntimeError("MAX Serve HTTP port not ready")

    print("PZAAS MAX HTTP PORT: READY", flush=True)

    req = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=180) as response:
        result = response.read()
        print("PZAAS HTTP STATUS:", response.status, flush=True)
        parsed = json.loads(result)
        print("PZAAS RESPONSE TYPE:", type(parsed).__name__)
        if isinstance(parsed, dict):
            print("PZAAS RESPONSE KEYS:", list(parsed))
        print("PZAAS BUILT-IN MAX HTTP 200: PASS", flush=True)

except Exception as exc:
    print("PZAAS HTTP BLOCKED:", repr(exc), flush=True)
    if isinstance(exc, urllib.error.HTTPError):
        print("ERROR BODY:", exc.read(1000).decode(errors="replace"))
    print("=== LAST 25 SERVER LOG LINES ===")
    print("\n".join(log.read_text(errors="replace").splitlines()[-25:]))
    raise SystemExit(1)

finally:
    server.terminate()
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()
PY
SH
