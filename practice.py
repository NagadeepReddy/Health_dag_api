python3 -B - <<'PY'
import json, subprocess

P = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

prefix = "a176e284b50a"
ids = subprocess.check_output(P + ["ps", "-q"], text=True).split()
matches = [x for x in ids if x.startswith(prefix)]

if len(matches) != 1:
    raise SystemExit("STOP: Expected native 8766 container not running")

cid = matches[0]
info = json.loads(subprocess.check_output(
    P + ["inspect", cid], text=True
))[0]

mounts = info.get("Mounts") or []
batch_mount = [
    m for m in mounts
    if m.get("Destination") == "/batch2"
    and "CTA_MAX_TRUE_BATCH2_DEV_20261029" in m.get("Source", "")
]

if len(batch_mount) != 1:
    raise SystemExit("STOP: Required Batch-2 mount unavailable")

code = r'''
import os
from pathlib import Path

args = [
    x.decode(errors="replace")
    for x in Path("/proc/1/cmdline").read_bytes().split(b"\0")
    if x
]

env = {}
for item in Path("/proc/1/environ").read_bytes().split(b"\0"):
    if b"=" in item:
        k, v = item.split(b"=", 1)
        if k == b"PYTHONPATH":
            env["PYTHONPATH"] = v.decode(errors="replace")

stage = Path(
    "/batch2/native_batch2_release_candidate/"
    "maxserve_cta_extension"
)

print("RUNNING ENTRYPOINT:", args[0] if args else "UNKNOWN")
print("LAUNCHER MODULES:", [
    a for a in args
    if any(x in a for x in (
        "cta_native_launcher",
        "max.entrypoints",
        "maxserve_cta_extension"
    ))
])
print("CLI OPTION NAMES:", [
    a for a in args if a.startswith("--")
])
print("PROCESS WORKDIR:", os.readlink("/proc/1/cwd"))
print("ACTIVE PYTHONPATH:", env.get("PYTHONPATH", "(unset)"))
print(
    "STAGED PATH CONFIGURED:",
    "/batch2/native_batch2_release_candidate"
    in env.get("PYTHONPATH", "")
)
print("STAGED LAUNCHER:", (stage / "cta_native_launcher.py").is_file())
print("STAGED WORKER HOOK:", (stage / "cta_worker_registration.py").is_file())
print("STAGED SCHEDULER:", (stage / "cta_native_scheduler.py").is_file())
print("REAL BATCH BACKEND:", Path(
    "/batch2/real_max_batch2_backend.py"
).is_file())
print("NATIVE LAUNCH CONFIGURATION: INSPECTED")
'''

r = subprocess.run(
    P + [
        "exec", "-i",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        cid, "/opt/venv/bin/python", "-B", "-"
    ],
    input=code,
    text=True,
    capture_output=True,
    timeout=30
)

print(r.stdout)
if r.stderr:
    print(r.stderr[-1200:])
print("EXIT CODE:", r.returncode)
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
