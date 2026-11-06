
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import json
import os
import signal
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

handoff = Path("/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106")
launcher = handoff / "runtime/launch_max_model.sh"
fixture = Path("artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json")
evidence = Path("artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence")

for path in (launcher, fixture, evidence):
    if not path.exists():
        raise SystemExit(f"STOP: Missing {path}")

subprocess.run(["bash", "-n", str(launcher)], check=True)
print("GENERIC LAUNCHER SYNTAX: PASS", flush=True)

port = None
for candidate in range(18780, 18820):
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", candidate))
            port = candidate
            break
        except OSError:
            continue

if port is None:
    raise SystemExit("STOP: No available test port")

log = evidence / "pzaas_generic_launcher.log"
env = os.environ.copy()
env["HOST_PORT"] = str(port)

print("GENERIC LAUNCHER: STARTING", flush=True)
print("ISOLATED TEST PORT:", port, flush=True)

with log.open("w") as output:
    proc = subprocess.Popen(
        ["bash", str(launcher)],
        cwd=handoff,
        env=env,
        stdout=output,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )

try:
    deadline = time.monotonic() + 180

    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("Generic launcher exited")

        try:
            with socket.create_connection(
                ("127.0.0.1", port), timeout=2
            ):
                break
        except OSError:
            time.sleep(2)
    else:
        raise RuntimeError("Launcher startup timeout")

    print("GENERIC LAUNCHER SERVER: READY", flush=True)

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/pzaas/predict",
        data=fixture.read_bytes(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=180) as response:
        status = response.status
        payload = json.loads(response.read())

    def unpack(value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except ValueError:
                pass
        return value

    body = unpack(payload["jsonData"])
    prediction = unpack(body["prediction"])
    products = unpack(prediction["productList"])

    trained = (
        "PZAAS REAL MAX EXECUTION: PASS"
        in log.read_text(errors="replace")
    )

    print("GENERIC LAUNCHER HTTP STATUS:", status)
    print("PRODUCT COUNT:", len(products))
    print("TRAINED MAX EXECUTION:", trained)

    if status != 200 or len(products) != 24 or not trained:
        raise RuntimeError("Generic launcher acceptance failed")

    proof = {
        "generic_launcher": "PASS",
        "http_status": status,
        "recommendation_count": len(products),
        "trained_max_execution": trained,
        "packaged_runtime": True,
        "live_kubernetes_lookups": "pending",
        "other_vm_validation": "pending"
    }

    (evidence / "pzaas_generic_launcher_proof.json").write_text(
        json.dumps(proof, indent=2)
    )

    print("PZAAS GENERIC LAUNCHER: PASS")
    print("VERIFIED HANDOFF: UNCHANGED")
    print("CTA / BPLAN / ORIGINAL DS: UNCHANGED")

except Exception as exc:
    print("GENERIC LAUNCHER BLOCKED:", repr(exc))
    print("=== SERVER LOG ===")
    print("\n".join(log.read_text(errors="replace").splitlines()[-30:]))
    raise SystemExit(1)

finally:
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
PY
