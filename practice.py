
cd /application1/sajjna8 && python3 - <<'PY'
import json
import subprocess
import tempfile
from pathlib import Path

base = Path("/application1/sajjna8")
stage = base / "max_shared_infra/isolated/cta_shared_wiring_v1"
shared = base / "max_shared_infra/python"
model = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")

print("=== CTA SHARED MAX LIVE HTTP ===", flush=True)

launchers = sorted(
    p for p in model.rglob("cta_native_launcher.py")
    if p.parent.name == "maxserve_cta_extension"
)

if len(launchers) != 1:
    raise SystemExit(
        f"STOP: Expected one CTA launcher, found {len(launchers)}"
    )

launcher = launchers[0]
relative = launcher.parent.relative_to(model)

for name in ("cta_native_launcher.py", "cta_spawn_worker.py",
             "cta_router.py"):
    if not (stage / name).is_file():
        raise SystemExit("STOP: Isolated CTA module missing: " + name)

if "WorkerLifecycle(" not in (stage / "cta_spawn_worker.py").read_text():
    raise SystemExit("STOP: Shared CTA worker not wired")

if "register_model_routes(" not in (stage / "cta_router.py").read_text():
    raise SystemExit("STOP: Shared CTA router not wired")

def requests_from_collection(obj):
    if isinstance(obj, dict):
        req = obj.get("request")
        if isinstance(req, dict) and req.get("method") == "POST":
            url = req.get("url", "")
            if isinstance(url, dict):
                url = url.get("raw", "")
            body = req.get("body", {})
            raw = body.get("raw") if isinstance(body, dict) else None
            if "cta" in str(url).lower() and isinstance(raw, str):
                try:
                    data = json.loads(raw)
                    if isinstance(data, dict):
                        yield data
                except ValueError:
                    pass
        for value in obj.values():
            yield from requests_from_collection(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from requests_from_collection(value)

payload = None
source = None
search_roots = [
    model,
    Path("/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031"),
    base / "rt-pzaas-cta-offers-v1",
]

for root in search_roots:
    if not root.is_dir():
        continue
    for path in sorted(root.rglob("*.json")):
        if not any(word in path.name.lower() for word in
                   ("postman", "collection")):
            continue
        if path.stat().st_size > 3000000:
            continue
        try:
            collection = json.loads(path.read_text())
            candidate = next(requests_from_collection(collection), None)
        except (OSError, ValueError):
            continue
        if candidate is not None:
            payload, source = candidate, path
            break
    if payload is not None:
        break

print("CTA LAUNCHER:", launcher, flush=True)
print("ISOLATED SHARED MODULES: VERIFIED", flush=True)

if payload is None:
    print("STOP: Original CTA Postman request not located")
    print("NO CONTAINERS STARTED")
    print("NO FILES MODIFIED")
    raise SystemExit(1)

print("ORIGINAL REQUEST SOURCE:", source, flush=True)

inside = r'''
import json, socket, subprocess, sys, time
import urllib.request, urllib.error
from pathlib import Path

logpath = Path("/tmp/cta_shared_server.log")
with logpath.open("w") as log:
    server = subprocess.Popen(
        [sys.executable, "-u", "-m",
         "maxserve_cta_extension.cta_native_launcher"],
        stdout=log, stderr=subprocess.STDOUT,
    )

    try:
        ready = False
        for _ in range(180):
            if server.poll() is not None:
                break
            try:
                with socket.create_connection(
                    ("127.0.0.1", 8000), timeout=1
                ):
                    ready = True
                    break
            except OSError:
                time.sleep(1)

        if not ready:
            raise RuntimeError("CTA server did not start")

        print("CTA SHARED MAX SERVER: READY", flush=True)

        body = Path("/tmp/cta_input.json").read_bytes()
        errors = []

        for route in ("/cta/predict", "/cta/infer"):
            request = urllib.request.Request(
                "http://127.0.0.1:8000" + route,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(
                    request, timeout=240
                ) as response:
                    data = json.loads(response.read())
                    if response.status != 200:
                        raise RuntimeError("Unexpected HTTP status")
                    if not isinstance(data, (dict, list)):
                        raise RuntimeError("Invalid JSON response")
                    if isinstance(data, dict) and "error" in data:
                        raise RuntimeError(str(data["error"]))

                    print("ROUTE:", route, flush=True)
                    print("HTTP STATUS:", response.status, flush=True)
                    print("CTA JSON RESPONSE: PASS", flush=True)
                    print("CTA SHARED MAX HTTP: PASS", flush=True)
                    break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode(errors="replace")
                errors.append(f"{route}: HTTP {exc.code} {detail[:200]}")
            except Exception as exc:
                errors.append(f"{route}: {exc}")
        else:
            raise RuntimeError("; ".join(errors))

    except Exception as exc:
        print("CTA SHARED MAX HTTP: BLOCKED", flush=True)
        print("ERROR:", exc, flush=True)
        log.flush()
        print("=== CTA SERVER LOG ===", flush=True)
        print("\n".join(
            logpath.read_text(errors="replace").splitlines()[-55:]
        ), flush=True)
        sys.exit(1)
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=8)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
'''

with tempfile.TemporaryDirectory(prefix="cta_shared_") as tmp:
    request_file = Path(tmp) / "cta_input.json"
    request_file.write_text(json.dumps(payload))
    request_file.chmod(0o644)

    parent = relative.parent.as_posix()
    pythonpath = ":".join([
        "/shared_infra/python",
        f"/workspace/{parent}",
        "/workspace",
        "/shared_deps",
        "/shared_deps/sklearn161",
    ])

    cmd = [
        "podman",
        "--root", "/application1/podman/storage",
        "--runroot", "/run/containers/storage",
        "run", "--rm", "--pull=never",
        "--network=none",
        "--memory=18g",
        "--pids-limit=512",
        "-v", f"{model}:/workspace:ro",
        "-v", f"{stage}:/workspace/{relative}:ro",
        "-v", f"{shared}:/shared_infra/python:ro",
        "-v", f"{request_file}:/tmp/cta_input.json:ro",
        "-w", "/workspace",
        "-e", f"PYTHONPATH={pythonpath}",
    ]

    deps = Path("/application1/max_shared_python_deps")
    if deps.is_dir():
        cmd += ["-v", f"{deps}:/shared_deps:ro"]

    cmd += [
        "--entrypoint", "/opt/venv/bin/python",
        "localhost/max-shared-runtime:cpu",
        "-u", "-c", inside,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=480
        )
    except subprocess.TimeoutExpired:
        raise SystemExit("STOP: CTA live HTTP test timed out")

    print((result.stdout + result.stderr)[-14000:], flush=True)

    if result.returncode:
        raise SystemExit("STOP: CTA shared HTTP not yet verified")

print("\n=== RESULT ===")
print("CTA SHARED HTTP: PASS")
print("ORIGINAL CTA HANDOFF: UNCHANGED")
print("BPLAN / PZAAS: UNCHANGED")
print("TEMPORARY CONTAINER: REMOVED")
print("NEXT: SIMULTANEOUS THREE-MODEL VALIDATION")
PY
