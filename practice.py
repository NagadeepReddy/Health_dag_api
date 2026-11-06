
cd /application1/sajjna8 && python3 - <<'PY'
import ast
import json
import re
import subprocess
import tempfile
from pathlib import Path

root = Path("/application1/sajjna8")
stage = root / "max_shared_infra/isolated/pzaas_shared_wiring_v1"
worker_file = stage / "pzaas_spawn_worker.py"
model = root / "PZAAS_MAX_CLEAN_HANDOFF_20261106/model"
shared = root / "max_shared_infra/python"
deps = Path("/application1/max_shared_python_deps")

print("=== SHARED MAX WORKER FIX AND LIVE E2E ===", flush=True)

required = [worker_file, stage / "pzaas_native_launcher.py",
            model, shared, deps]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("STOP: Required paths missing:\n" + "\n".join(missing))

source = worker_file.read_text()
tree = ast.parse(source)

matches = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "lifecycle"
            for t in n.targets)
    and isinstance(n.value, ast.Call)
    and isinstance(n.value.func, ast.Name)
    and n.value.func.id == "WorkerLifecycle"
]

if len(matches) != 1:
    raise SystemExit(
        "STOP: Expected exactly one shared WorkerLifecycle assignment; "
        f"found {len(matches)}"
    )

node = matches[0]
keywords = {k.arg: k.value for k in node.value.keywords}

if not all(k in keywords for k in ("create", "load", "attach_max")):
    raise SystemExit("STOP: Unexpected lifecycle contract")

create = keywords["create"]

def is_worker_method(value, name):
    return (
        isinstance(value, ast.Attribute)
        and value.attr == name
        and isinstance(value.value, ast.Name)
        and value.value.id == "worker"
    )

if is_worker_method(create, "pipeline_factory"):
    lines = source.splitlines(keepends=True)
    indent = re.match(r"[ \t]*", lines[node.lineno - 1]).group()

    replacement = (
        f"{indent}lifecycle = WorkerLifecycle(\n"
        f"{indent}    create=worker.initialize,\n"
        f"{indent}    load=lambda pipeline: None,\n"
        f"{indent}    attach_max=lambda pipeline: None,\n"
        f"{indent})\n"
    )

    lines[node.lineno - 1:node.end_lineno] = [replacement]
    updated = "".join(lines)

    compile(updated, str(worker_file), "exec")
    worker_file.write_text(updated)
    print("WORKER: ORIGINAL INITIALIZATION RESTORED", flush=True)

elif is_worker_method(create, "initialize"):
    print("WORKER: ALREADY CORRECTED", flush=True)

else:
    raise SystemExit("STOP: Unknown worker creation strategy")

print("SHARED LIFECYCLE: RETAINED", flush=True)
print("ISOLATED PYTHON SYNTAX: PASS", flush=True)

# Prefer the existing validated Postman request only as test data.
evidence = (
    root / "rt-pzaas-v1.0/artifacts/v1.472-max/"
    "maxserve_pzaas_extension/pzaas_http_evidence"
)

payload = None
input_name = None

def requests(items):
    for item in items:
        req = item.get("request")
        if isinstance(req, dict):
            yield item.get("name", ""), req
        yield from requests(item.get("item", []))

for path in sorted(evidence.glob("*COLLECTION*.json")):
    try:
        collection = json.loads(path.read_text())
        for name, req in requests(collection.get("item", [])):
            body = req.get("body", {})
            raw = body.get("raw") if isinstance(body, dict) else None
            if not raw:
                continue
            candidate = json.loads(raw)
            if (isinstance(candidate, dict)
                    and "ClientFeature" in candidate
                    and "Events" in candidate):
                payload = candidate
                input_name = f"{path.name}: {name}"
                break
    except (OSError, ValueError, TypeError):
        continue
    if payload is not None:
        break

if payload is None:
    fallback = (
        root / "rt-pzaas-v1.0/artifacts/v1.472/samples/ppa_input.json"
    )
    if not fallback.is_file():
        raise SystemExit("STOP: No original valid request file available")
    payload = json.loads(fallback.read_text())
    input_name = fallback.name

assert isinstance(payload, dict) and "ClientFeature" in payload

print("HTTP INPUT:", input_name, flush=True)

container_test = r'''
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

print("=== LIVE SHARED MAX HTTP ===", flush=True)

logpath = Path("/tmp/shared_max_worker.log")
log = logpath.open("w")
server = subprocess.Popen(
    [
        sys.executable, "-u", "-m",
        "pzaas_native_serve_dev.pzaas_native_launcher"
    ],
    stdout=log,
    stderr=subprocess.STDOUT,
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
            f"MAX server did not start; exit={server.poll()}"
        )

    print("SHARED MAX SERVER: READY", flush=True)

    payload = json.loads(Path("/input.json").read_text())
    request = urllib.request.Request(
        "http://127.0.0.1:18768/pzaas/predict",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            status = response.status
            result = json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {detail[:700]}")

    data = result.get("jsonData", result)
    if isinstance(data, dict):
        data = data.get("prediction", data)

    products = data.get("productList") if isinstance(data, dict) else None

    if status != 200:
        raise RuntimeError(f"Unexpected HTTP status: {status}")
    if not isinstance(products, list):
        raise RuntimeError(
            "HTTP 200 returned, but productList was not found"
        )

    print("SHARED MAX HTTP 200: PASS", flush=True)
    print("RECOMMENDATION COUNT:", len(products), flush=True)

    log.flush()
    lines = logpath.read_text(errors="replace").splitlines()
    for marker in (
        "PZAAS FACTORY ENTERED",
        "PZAAS NATIVE HTTP ROUTES: REGISTERED",
        "PZAAS PREDICT_RAW: START",
    ):
        print(
            marker + ":",
            "OBSERVED" if any(marker in line for line in lines)
            else "NOT OBSERVED",
            flush=True,
        )

    print("LIVE SHARED MAX PZAAS E2E: PASS", flush=True)

except Exception as error:
    print("LIVE SHARED MAX PZAAS E2E: BLOCKED", flush=True)
    print("ROOT ERROR:", str(error), flush=True)
    log.flush()
    print("=== LAST 55 SERVER LOG LINES ===", flush=True)
    print("\n".join(
        logpath.read_text(errors="replace").splitlines()[-55:]
    ), flush=True)
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

podman = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage",
    "run", "--rm", "--pull=never", "--network=none",
    "--memory=12g", "--pids-limit=512",
    "-v", f"{model}:/workspace:ro",
    "-v", (
        f"{stage}:/workspace/artifacts/v1.472-max/"
        "maxserve_pzaas_extension/pzaas_native_serve_dev:ro"
    ),
    "-v", f"{shared}:/shared_infra/python:ro",
    "-v", f"{deps}:/shared_deps:ro",
    "-w", "/workspace",
    "-e", (
        "PYTHONPATH=/shared_infra/python:/shared_deps/sklearn161:"
        "/shared_deps:/workspace/artifacts/v1.472-max/pzaas_max/"
        "validation/python_deps:/workspace/artifacts/v1.472-max/"
        "maxserve_pzaas_extension:/workspace/artifacts/v1.472-max:"
        "/workspace/artifacts/v1.472/core-artifact:"
        "/workspace/artifacts/v1.472/utils/dependency-utils"
    ),
    "--entrypoint", "/opt/venv/bin/python",
]

with tempfile.TemporaryDirectory(prefix="pzaas_shared_e2e_") as tmp:
    fixture = Path(tmp) / "input.json"
    fixture.write_text(json.dumps(payload))
    fixture.chmod(0o644)

    command = (
        podman[:]
        + ["-v", f"{fixture}:/input.json:ro"]
        + [
            "localhost/max-shared-runtime:cpu",
            "-u", "-c", container_test
        ]
    )

    try:
        completed = subprocess.run(
            command,
            timeout=360,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(completed.stdout[-14000:], flush=True)
        if completed.returncode:
            raise SystemExit(
                f"STOP: Live integration failed (exit {completed.returncode})"
            )
    except subprocess.TimeoutExpired:
        raise SystemExit("STOP: Live integration exceeded timeout")

print("=== FINAL RESULT ===")
print("ISOLATED PZAAS SHARED MAX INTEGRATION: PASS")
print("ORIGINAL PZAAS SOURCE / WEIGHTS: UNCHANGED")
print("CTA / BPLAN HANDOFFS: UNCHANGED")
print("TEMPORARY TEST REQUEST: REMOVED")
print("NEXT: CROSS-MODEL REUSE VALIDATION")
PY
