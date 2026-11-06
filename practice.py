
cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
set -euo pipefail

STAGE="/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106"
EVIDENCE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence"
FIXTURE="$PWD/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json"
NAME="pzaas-clean-postman-20261106"

test -d "$STAGE"
test -f "$FIXTURE"
test -d "$EVIDENCE"

python3 - "$FIXTURE" "$EVIDENCE" <<'PY'
import json
import sys
from pathlib import Path

fixture = Path(sys.argv[1])
evidence = Path(sys.argv[2])

body = json.loads(fixture.read_text())

collection = {
    "info": {
        "name": "PZAAS v1.472 Clean MAX Serve",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [{
        "name": "PZAAS Predict",
        "request": {
            "method": "POST",
            "header": [
                {"key": "Content-Type", "value": "application/json"}
            ],
            "url": "http://127.0.0.1:18769/pzaas/predict",
            "body": {
                "mode": "raw",
                "raw": json.dumps(body, indent=2),
                "options": {"raw": {"language": "json"}}
            }
        }
    }]
}

output = evidence / "PZAAS_CLEAN_MAX_POSTMAN_COLLECTION.json"

if output.exists():
    raise SystemExit("STOP: Postman collection already exists")

output.write_text(json.dumps(collection, indent=2))

print("POSTMAN COLLECTION: CREATED")
print("FILE:", output)
print("ORIGINAL TEST FIXTURE: UNCHANGED")
PY

if podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  container exists "$NAME"; then
  echo "STOP: Postman container name already exists"
  exit 1
fi

python3 - <<'PY'
import socket
with socket.socket() as sock:
    try:
        sock.bind(("127.0.0.1", 18769))
    except OSError as exc:
        raise SystemExit(f"STOP: Host port 18769 unavailable: {exc}")
print("HOST PORT 18769: AVAILABLE")
PY

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -d --pull=never \
  --name "$NAME" \
  --memory=12g --pids-limit=512 \
  -p 127.0.0.1:18769:18768 \
  -v "$STAGE:/workspace:ro" \
  -v /application1/max_shared_python_deps:/shared_deps:ro \
  -w /workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/shared_deps/sklearn161:/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension:/workspace/artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev:/workspace/artifacts/v1.472-max:/workspace/artifacts/v1.472/core-artifact:/workspace/artifacts/v1.472/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -m pzaas_native_serve_dev.pzaas_native_launcher

python3 - "$NAME" <<'PY'
import socket
import subprocess
import sys
import time

name = sys.argv[1]
podman = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

for _ in range(75):
    result = subprocess.run(
        podman + [
            "inspect", "--format", "{{.State.Running}}", name
        ],
        capture_output=True, text=True
    )

    if result.stdout.strip() != "true":
        print("POSTMAN SERVER: EXITED")
        break

    try:
        with socket.create_connection(
            ("127.0.0.1", 18769), timeout=2
        ):
            print("PZAAS POSTMAN SERVER: READY")
            print("VM PORT: 18769")
            print("ENDPOINT: http://127.0.0.1:18769/pzaas/predict")
            print("ORIGINAL DS / MAX IMAGE: UNCHANGED")
            sys.exit(0)
    except OSError:
        time.sleep(2)

logs = subprocess.run(
    podman + ["logs", "--tail", "35", name],
    capture_output=True, text=True
)

print("=== SERVER LOG ===")
print(logs.stdout)
print(logs.stderr)
raise SystemExit("POSTMAN SERVER: NOT READY")
PY
SH
