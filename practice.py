
cd /application1/sajjna8 && python3 - <<'PY'
import json
import os
import signal
import socket
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

root = Path("/application1/sajjna8/max_shared_infra")
package = Path("/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106")
fixture = Path(
    "/application1/sajjna8/rt-pzaas-v1.0/"
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json"
)

launcher = root / "bin/run_max_model.sh"
evidence = root / "analysis"

for path in (
    launcher,
    package / "model",
    package / "runtime/python_deps",
    package / "config/model.env",
    fixture,
):
    if not path.exists():
        raise SystemExit(f"STOP: Required input missing: {path}")

subprocess.run(
    ["bash", "-n", str(launcher)],
    check=True
)

port = None
for candidate in range(18810, 18841):
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", candidate))
            port = candidate
            break
        except OSError:
            pass

if port is None:
    raise SystemExit("STOP: No free test port")

evidence.mkdir(parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
log = evidence / f"shared_pzaas_e2e_{stamp}.log"
proof = evidence / f"shared_pzaas_e2e_{stamp}.json"

env = os.environ.copy()
env["HOST_PORT"] = str(port)

print("=== INDEPENDENT SHARED MAX INTEGRATION ===", flush=True)
print("SHARED LAUNCHER:", launcher, flush=True)
print("VERIFIED MODEL PACKAGE:", package, flush=True)
print("TEST PORT:", port, flush=True)

with log.open("w") as stream:
    server = subprocess.Popen(
        ["bash", str(launcher), "start", str(package)],
        env=env,
        cwd=str(root),
        stdout=stream,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

try:
    deadline = time.monotonic() + 180

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Shared launcher exited")

        try:
            with socket.create_connection(
                ("127.0.0.1", port), timeout=2
            ):
                break
        except OSError:
            time.sleep(2)
    else:
        raise RuntimeError("Shared launcher startup timeout")

    print("SHARED INFRA SERVER: READY", flush=True)

    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/pzaas/predict",
        data=fixture.read_bytes(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(
        request, timeout=180
    ) as response:
        status = response.status
        result = json.loads(response.read())

    def unpack(value):
        if isinstance(value, str):
            return json.loads(value)
        return value

    data = unpack(result["jsonData"])
    prediction = unpack(data["prediction"])
    products = unpack(prediction["productList"])

    if not isinstance(products, list):
        raise RuntimeError("Invalid productList response")

    trained = False
    for _ in range(20):
        if "PZAAS REAL MAX EXECUTION: PASS" in log.read_text(
            errors="replace"
        ):
            trained = True
            break
        time.sleep(0.5)

    print("HTTP STATUS:", status, flush=True)
    print("RECOMMENDATIONS:", len(products), flush=True)
    print("TRAINED MAX EXECUTION:", trained, flush=True)

    if status != 200 or len(products) != 24 or not trained:
        raise RuntimeError("Shared infrastructure acceptance failed")

    proof.write_text(json.dumps({
        "shared_launcher": "PASS",
        "model": "PZAAS v1.472",
        "http_status": status,
        "recommendations": len(products),
        "trained_max_execution": trained,
        "model_package_modified": False,
        "shared_python_modules_wired": False,
        "live_kubernetes_lookups": "not validated"
    }, indent=2))

    print("\n=== RESULT ===")
    print("SHARED INFRA REAL MODEL SERVING: PASS")
    print("PZAAS HTTP 200: PASS")
    print("24 RECOMMENDATIONS: PASS")
    print("TRAINED MAX INFERENCE: PASS")
    print("SHARED PYTHON MODULE WIRING: PENDING")
    print("CTA / BPLAN / PZAAS HANDOFFS: UNCHANGED")
    print("PROOF:", proof)

except Exception as exc:
    print("SHARED INTEGRATION BLOCKED:", repr(exc))
    print("=== LAST 30 LOG LINES ===")
    print("\n".join(
        log.read_text(errors="replace").splitlines()[-30:]
    ))
    raise SystemExit(1)

finally:
    if server.poll() is None:
        os.killpg(server.pid, signal.SIGTERM)
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(server.pid, signal.SIGKILL)
            server.wait()
PY
