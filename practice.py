
cd /application1/sajjna8 && python3 - <<'PY'
import json
import os
import signal
import socket
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

root = Path("/application1/sajjna8/max_shared_infra")
package = Path("/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106")
launcher = root / "bin/run_max_model_shared.sh"
shim = root / "integrations/pzaas/pzaas_queue_compat.py"
relative = (
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev/pzaas_queue_compat.py"
)
fixture = Path(
    "/application1/sajjna8/rt-pzaas-v1.0/"
    "artifacts/v1.472-max/maxserve_pzaas_extension/"
    "pzaas_native_serve_dev/pzaas_adjusted_sanity_input.json"
)
analysis = root / "analysis"

for path in (launcher, shim, fixture, package / "model" / relative):
    if not path.is_file():
        raise SystemExit(f"STOP: Required file missing: {path}")

analysis.mkdir(parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
log = analysis / f"shared_queue_http_{stamp}.log"
proof = analysis / f"shared_queue_http_{stamp}.json"

# Instrument a temporary copy of the already-tested adapter.
source = shim.read_text()
hook = "    return install_max_typed_response_queue("
if source.count(hook) != 1:
    raise SystemExit("STOP: Shared adapter structure changed")

source = source.replace(
    hook,
    '    print("SHARED_QUEUE_BINDING_EXECUTED", flush=True)\n' + hook,
    1,
)

probe_path = None
test_launcher = None
server = None

try:
    fd, name = tempfile.mkstemp(
        prefix="queue_probe_", suffix=".py", dir=analysis
    )
    probe_path = Path(name)
    with os.fdopen(fd, "w") as stream:
        stream.write(source)

    # Add the read-only overlay to a temporary launcher.
    code = launcher.read_text()
    needle = '  -v "$SHARED_PYTHON:/shared_runtime:ro" \\\n'

    if code.count(needle) != 1:
        raise RuntimeError("Shared launcher mount point changed")

    extra = (
        f'  -v "{probe_path}:/workspace/{relative}:ro" \\\n'
    )
    code = code.replace(needle, needle + extra, 1)

    fd, name = tempfile.mkstemp(
        prefix=".run_shared_queue_",
        suffix=".sh",
        dir=root / "bin",
    )
    test_launcher = Path(name)

    with os.fdopen(fd, "w") as stream:
        stream.write(code)

    test_launcher.chmod(0o700)
    subprocess.run(
        ["bash", "-n", str(test_launcher)],
        check=True,
    )

    port = None
    for candidate in range(18820, 18861):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", candidate))
                port = candidate
                break
            except OSError:
                continue

    if port is None:
        raise RuntimeError("No free isolated test port")

    env = os.environ.copy()
    env["HOST_PORT"] = str(port)

    print("=== LIVE SHARED QUEUE PZAAS HTTP TEST ===", flush=True)
    print("HOST PORT:", port, flush=True)
    print("VERIFIED HANDOFF: READ-ONLY", flush=True)
    print("SHARED QUEUE OVERLAY: ENABLED", flush=True)

    with log.open("w") as stream:
        server = subprocess.Popen(
            ["bash", str(test_launcher), "start", str(package)],
            cwd=str(root),
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    deadline = time.monotonic() + 180

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Model server exited during startup")
        try:
            with socket.create_connection(
                ("127.0.0.1", port), timeout=2
            ):
                break
        except OSError:
            time.sleep(2)
    else:
        raise RuntimeError("Server startup timeout")

    print("SHARED MAX SERVER: READY", flush=True)

    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/pzaas/predict",
        data=fixture.read_bytes(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({})
    )

    with opener.open(request, timeout=180) as response:
        status = response.status
        result = json.loads(response.read())

    def unpack(value):
        return json.loads(value) if isinstance(value, str) else value

    data = unpack(result["jsonData"])
    prediction = unpack(data["prediction"])
    products = unpack(prediction["productList"])

    if not isinstance(products, list):
        raise RuntimeError("Invalid productList")

    shared_active = False
    trained_max = False

    for _ in range(30):
        content = log.read_text(errors="replace")
        shared_active = "SHARED_QUEUE_BINDING_EXECUTED" in content
        trained_max = "PZAAS REAL MAX EXECUTION: PASS" in content
        if shared_active and trained_max:
            break
        time.sleep(0.5)

    print("HTTP STATUS:", status, flush=True)
    print("RECOMMENDATIONS:", len(products), flush=True)
    print("SHARED QUEUE HOOK USED:", shared_active, flush=True)
    print("TRAINED MAX EXECUTION:", trained_max, flush=True)

    if not (
        status == 200
        and len(products) == 24
        and shared_active
        and trained_max
    ):
        raise RuntimeError("Shared queue HTTP acceptance failed")

    proof.write_text(json.dumps({
        "model": "PZAAS v1.472",
        "http_status": status,
        "recommendations": len(products),
        "shared_queue_active": shared_active,
        "trained_max_execution": trained_max,
        "handoff_modified": False,
        "live_kubernetes_lookups": "not validated",
    }, indent=2))

    print("\n=== RESULT ===")
    print("REAL HTTP WITH SHARED QUEUE: PASS")
    print("PZAAS HTTP 200: PASS")
    print("TRAINED MAX INFERENCE: PASS")
    print("SHARED QUEUE MODULE: ACTIVELY USED")
    print("CTA / BPLAN / PZAAS HANDOFFS: UNCHANGED")
    print("EVIDENCE:", proof)

except Exception as exc:
    print("TEST BLOCKED:", repr(exc), flush=True)
    if log.exists():
        print("=== LAST 35 SERVER LOG LINES ===")
        print("\n".join(
            log.read_text(errors="replace").splitlines()[-35:]
        ))
    raise SystemExit(1)

finally:
    if server is not None and server.poll() is None:
        try:
            os.killpg(server.pid, signal.SIGTERM)
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(server.pid, signal.SIGKILL)
            server.wait()
        except ProcessLookupError:
            pass

    for path in (test_launcher, probe_path):
        if path is not None:
            path.unlink(missing_ok=True)

    print("TEMPORARY OVERLAYS: REMOVED", flush=True)
PY
