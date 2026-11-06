cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

python3 - <<'PYFIX'
from pathlib import Path
import ast
import shutil

file = Path(
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev/pzaas_max_model_adapter.py"
)

source = file.read_text()

old = "        self.pack = pack"
new = "        self.pack = _pzaas_pack72"
required = "from pzaas_live_pack_72 import pack as _pzaas_pack72"

if required not in source:
    raise SystemExit("STOP: Verified 72-input helper import missing")

if source.count(old) == 1:
    updated = source.replace(old, new, 1)
    ast.parse(updated, filename=str(file))

    backup = file.with_suffix(".py.before_pack72")
    if not backup.exists():
        shutil.copy2(file, backup)

    file.write_text(updated)
    print("PZAAS NATIVE 72-INPUT WIRING: FIXED")

elif source.count(new) == 1:
    print("PZAAS NATIVE 72-INPUT WIRING: ALREADY FIXED")

else:
    raise SystemExit("STOP: Unexpected adapter structure")

ast.parse(file.read_text(), filename=str(file))
print("PZAAS ADAPTER SYNTAX: PASS")
print("ORIGINAL DS / WEIGHTS / MAX IMAGE: UNCHANGED")
PYFIX

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network=none \
  --memory=12g --pids-limit=512 \
  -v "$PWD:/workspace:ro" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /workspace \
  -e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PYTEST'
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

if not fixture.is_file():
    raise SystemExit("STOP: Previously corrected fixture missing")

log = Path("/tmp/pzaas_verified72_http.log")

print("PZAAS VERIFIED 72-INPUT HTTP TEST: START", flush=True)

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
            raise RuntimeError("Native MAX server exited")

        try:
            with socket.create_connection(
                ("127.0.0.1", 18768), timeout=2
            ):
                break
        except OSError:
            time.sleep(2)
    else:
        raise RuntimeError("Native MAX HTTP startup timeout")

    print("PZAAS NATIVE MAX HTTP PORT: READY", flush=True)

    request = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=fixture.read_bytes(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(
        request, timeout=180
    ) as response:
        body = response.read()
        print("PZAAS HTTP STATUS:", response.status)
        parsed = json.loads(body)

        print("PZAAS JSON TYPE:", type(parsed).__name__)

        if isinstance(parsed, dict):
            print("PZAAS JSON KEYS:", list(parsed.keys()))

        print("PZAAS NATIVE MAX HTTP 200: PASS")

except Exception as exc:
    print("PZAAS HTTP BLOCKED:", repr(exc), flush=True)

    if isinstance(exc, urllib.error.HTTPError):
        print(
            "HTTP ERROR BODY:",
            exc.read(1200).decode(errors="replace")
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
PYTEST
SH
