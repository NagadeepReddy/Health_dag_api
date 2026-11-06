
cd /application1/sajjna8 && python3 - <<'PY'
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

base = Path("/application1/sajjna8")
model = base / "PZAAS_MAX_CLEAN_HANDOFF_20261106/model"
stage = base / "max_shared_infra/isolated/pzaas_shared_wiring_v1"
rel = Path("artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_native_serve_dev")
original = model / rel
repo = base / "rt-pzaas-v1.0"
collection = repo / "artifacts/v1.472-max/maxserve_pzaas_extension/pzaas_http_evidence/PZAAS_CLEAN_MAX_POSTMAN_COLLECTION.json"

print("=== SHARED MAX IMPORT REPAIR ===", flush=True)

for path in (original, stage, collection):
    if not path.exists():
        raise SystemExit(f"STOP: Required path missing: {path}")

# Restore support files masked by the isolated directory mount.
copied = []
for source in sorted(original.glob("*.py")):
    target = stage / source.name
    if not target.exists():
        shutil.copy2(source, target)
        copied.append(source.name)

adapter = stage / "pzaas_worker_adapter.py"

if not adapter.exists():
    candidates = (
        list(model.rglob("pzaas_worker_adapter.py"))
        + list(repo.rglob("pzaas_worker_adapter.py"))
    )
    if not candidates:
        raise SystemExit(
            "STOP: pzaas_worker_adapter.py missing from both "
            "the clean model and original repository"
        )
    candidates.sort(key=lambda p: (
        0 if model in p.parents else 1,
        len(p.parts)
    ))
    shutil.copy2(candidates[0], adapter)
    copied.append(adapter.name)

for name in (
    "pzaas_native_launcher.py",
    "pzaas_spawn_worker.py",
    "pzaas_max_model_adapter.py",
    "pzaas_worker_adapter.py",
):
    path = stage / name
    if not path.exists():
        raise SystemExit(f"STOP: Required isolated module missing: {name}")
    compile(path.read_text(), str(path), "exec")

print("RESTORED SUPPORT FILES:", copied or "ALREADY PRESENT", flush=True)
print("ISOLATED SYNTAX: PASS", flush=True)
print("ORIGINAL MODEL: UNCHANGED", flush=True)

data = json.loads(collection.read_text())

def find_request(items):
    for item in items:
        req = item.get("request", {})
        if isinstance(req, dict):
            raw = req.get("body", {}).get("raw")
            if raw:
                try:
                    body = json.loads(raw)
                    if isinstance(body, dict) and "ClientFeature" in body:
                        return body
                except (ValueError, TypeError):
                    pass
        nested = find_request(item.get("item", []))
        if nested is not None:
            return nested
    return None

payload = find_request(data.get("item", []))
if payload is None:
    raise SystemExit("STOP: No valid original Postman request")

test = r'''
import json
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
import importlib.util
from pathlib import Path

print("=== LIVE SHARED MAX TEST ===", flush=True)

for name in ("pzaas_worker_adapter", "max_runtime_shared"):
    if importlib.util.find_spec(name) is None:
        raise SystemExit("STOP: Python cannot locate " + name)

print("MODEL ADAPTER IMPORT PATH: PASS", flush=True)
print("SHARED MODULE IMPORT PATH: PASS", flush=True)

logpath = Path("/tmp/pzaas_shared_worker.log")
log = logpath.open("w")

server = subprocess.Popen(
    [sys.executable, "-u", "-m",
     "pzaas_native_serve_dev.pzaas_native_launcher"],
    stdout=log,
    stderr=subprocess.STDOUT
)

try:
    ready = False
    for _ in range(150):
        if server.poll() is not None:
            break
        try:
            with socket.create_connection(
                ("127.0.0.1", 18768), timeout=1
            ):
                ready = True
                break
        except OSError:
            time.sleep(1)

    if not ready:
        raise RuntimeError(
            f"Server startup failed: exit={server.poll()}"
        )

    print("SHARED MAX SERVER: READY", flush=True)

    body = json.loads(Path("/input.json").read_text())
    request = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            status = response.status
            result = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"HTTP {error.code}: "
            + error.read().decode(errors="replace")[:500]
        )

    print("HTTP STATUS:", status, flush=True)
    if status != 200:
        raise RuntimeError("Expected HTTP 200")

    output = result.get("jsonData", result)
    if isinstance(output, dict):
        output = output.get("prediction", output)

    products = (
        output.get("productList")
        if isinstance(output, dict) else None
    )

    if not isinstance(products, list):
        raise RuntimeError("Missing productList in response")

    print("RECOMMENDATIONS:", len(products), flush=True)

    if len(products) != 24:
        raise RuntimeError("Expected 24 recommendations")

    print("LIVE SHARED MAX HTTP: PASS", flush=True)

except Exception as exc:
    print("LIVE SHARED MAX HTTP: BLOCKED", flush=True)
    print("ERROR:", str(exc), flush=True)
    log.flush()
    lines = logpath.read_text(errors="replace").splitlines()
    root_errors = [
        line for line in lines
        if any(term in line for term in (
            "ModuleNotFoundError",
            "ImportError",
            "FileNotFoundError",
            "AttributeError",
            "RuntimeError",
            "Traceback",
        ))
    ]
    print("=== ROOT ERROR LINES ===", flush=True)
    print("\n".join(root_errors[:12]), flush=True)
    print("=== LAST 30 SERVER LINES ===", flush=True)
    print("\n".join(lines[-30:]), flush=True)
    sys.exit(1)

finally:
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
    log.close()
'''

pythonpath = ":".join([
    "/shared_infra/python",
    "/shared_deps/sklearn161",
    "/shared_deps",
    "/workspace/" + str(rel),
    "/workspace/artifacts/v1.472-max/pzaas_max/validation/python_deps",
    "/workspace/artifacts/v1.472-max/maxserve_pzaas_extension",
    "/workspace/artifacts/v1.472-max",
    "/workspace/artifacts/v1.472/core-artifact",
    "/workspace/artifacts/v1.472/utils/dependency-utils",
])

with tempfile.TemporaryDirectory(prefix="shared_max_test_") as tmp:
    fixture = Path(tmp) / "input.json"
    fixture.write_text(json.dumps(payload))
    fixture.chmod(0o644)

    command = [
        "podman",
        "--root", "/application1/podman/storage",
        "--runroot", "/run/containers/storage",
        "run", "--rm", "--pull=never",
        "--network=none", "--memory=12g",
        "--pids-limit=512",
        "-v", f"{model}:/workspace:ro",
        "-v", f"{stage}:/workspace/{rel}:ro",
        "-v", f"{base}/max_shared_infra/python:/shared_infra/python:ro",
        "-v", "/application1/max_shared_python_deps:/shared_deps:ro",
        "-v", f"{fixture}:/input.json:ro",
        "-w", "/workspace",
        "-e", "PYTHONPATH=" + pythonpath,
        "--entrypoint", "/opt/venv/bin/python",
        "localhost/max-shared-runtime:cpu",
        "-u", "-c", test,
    ]

    try:
        outcome = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=360
        )
    except subprocess.TimeoutExpired:
        raise SystemExit("STOP: Live test timed out")

    print(outcome.stdout[-14000:], flush=True)

    if outcome.returncode != 0:
        raise SystemExit("STOP: Live E2E still blocked")

print("=== RESULT ===")
print("SHARED MAX PZAAS HTTP: PASS")
print("ORIGINAL DS / CTA / BPLAN: UNCHANGED")
print("NEXT: CROSS-MODEL LIVE ADOPTION")
PY
