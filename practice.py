python3 -B - <<'PY'
import json
import subprocess

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

targets = {
    "0c95d4a8f887": 8765,
    "a176e284b50a": 8766,
}

running = subprocess.check_output(
    P + ["ps", "-q"], text=True
).split()

probe = r'''
import os
import socket
import urllib.request
import urllib.error
from pathlib import Path

stage = Path(
    "/batch2/native_batch2_release_candidate/"
    "maxserve_cta_extension"
)

print("STAGED PACKAGE VISIBLE:", stage.is_dir(), flush=True)

native_processes = []

for p in Path("/proc").iterdir():
    if not p.name.isdigit():
        continue
    try:
        cmd = (p / "cmdline").read_bytes().replace(b"\0", b" ")
        markers = (
            b"cta_native_launcher",
            b"max.entrypoints.pipelines",
            b"maxserve_cta_extension",
        )
        if not any(x in cmd for x in markers):
            continue

        env = (p / "environ").read_bytes()
        staged = b"/batch2/native_batch2_release_candidate" in env

        native_processes.append((p.name, staged))
    except (OSError, PermissionError):
        continue

print("NATIVE PROCESS COUNT:", len(native_processes))
for pid, staged in native_processes:
    print("PROCESS PID:", pid)
    print("STAGED PYTHONPATH:", staged)

port = TARGET_PORT

try:
    with socket.create_connection(("127.0.0.1", port), timeout=2):
        print("TCP LISTENER:", port, "PASS")

    url = f"http://127.0.0.1:{port}/v2/cta/probe"
    request = urllib.request.Request(url, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            print("CTA PROBE HTTP STATUS:", response.status)
    except urllib.error.HTTPError as exc:
        print("CTA PROBE HTTP STATUS:", exc.code)
    except Exception as exc:
        print("CTA PROBE:", type(exc).__name__)

except OSError:
    print("TCP LISTENER:", port, "NOT REACHABLE")

print("NO MODEL INFERENCE REQUESTS SENT")
'''

for prefix, port in targets.items():
    ids = [cid for cid in running if cid.startswith(prefix)]

    print("\n=== CONTAINER", prefix, "===")

    if len(ids) != 1:
        print("STOP: Container not uniquely running")
        continue

    cid = ids[0]
    info = json.loads(subprocess.check_output(
        P + ["inspect", cid], text=True
    ))[0]

    mounts = info.get("Mounts") or []
    staged_mount = any(
        m.get("Destination") == "/batch2"
        and "CTA_MAX_TRUE_BATCH2_DEV_20261029"
            in m.get("Source", "")
        for m in mounts
    )

    print("BATCH-2 DEVELOPMENT MOUNT:", staged_mount)
    print("NETWORK:", info.get("HostConfig", {}).get("NetworkMode"))

    code = probe.replace("TARGET_PORT", str(port))

    try:
        r = subprocess.run(
            P + [
                "exec", "-i",
                "-e", "PYTHONDONTWRITEBYTECODE=1",
                cid, "/opt/venv/bin/python", "-B", "-"
            ],
            input=code,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20
        )

        print(r.stdout[-2500:])
        print("INSPECTION EXIT CODE:", r.returncode)

    except subprocess.TimeoutExpired:
        print("STOP: Read-only inspection timed out")

print("\nORIGINAL DS/MAX: UNCHANGED")
print("WORKING RELEASE: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
