python3 -B - <<'PY'
import subprocess, json

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

ids = subprocess.check_output(P + ["ps", "-q"], text=True).split()
matches = [x for x in ids if x.startswith("a176e284b50a")]

if len(matches) != 1:
    raise SystemExit("STOP: Existing 8766 container unavailable")

code = r'''
import os
from pathlib import Path

args = [
    a.decode(errors="replace")
    for a in Path("/proc/1/cmdline").read_bytes().split(b"\0")
    if a
]

env = {}
for entry in Path("/proc/1/environ").read_bytes().split(b"\0"):
    if b"=" in entry:
        key, value = entry.split(b"=", 1)
        if key == b"PYTHONPATH":
            env["PYTHONPATH"] = value.decode(errors="replace")

stage = Path(
    "/batch2/native_batch2_release_candidate/"
    "maxserve_cta_extension"
)

print("=== EXISTING NATIVE MAX SERVE ===")
print("PROCESS WORKDIR:", os.readlink("/proc/1/cwd"))
print("ACTIVE PYTHONPATH:", env.get("PYTHONPATH", "(unset)"))
print("STAGED PACKAGE VISIBLE:", stage.is_dir())

print("=== LAUNCH ARGUMENTS ===")
sensitive = False
for i, value in enumerate(args):
    if sensitive:
        print(i, "<redacted>")
        sensitive = False
        continue
    if any(x in value.lower() for x in
           ("password", "secret", "token", "api-key")):
        print(i, "<redacted>")
        if value.startswith("-") and "=" not in value:
            sensitive = True
    else:
        print(i, value)

print("=== STAGED ENTRYPOINT ===")
print("LAUNCHER PRESENT:",
      (stage / "cta_native_launcher.py").is_file())
print("WORKER HOOK PRESENT:",
      (stage / "cta_worker_registration.py").is_file())
print("BATCH SCHEDULER PRESENT:",
      (stage / "cta_native_scheduler.py").is_file())
print("BACKEND PRESENT:",
      Path("/batch2/real_max_batch2_backend.py").is_file())

print("LAUNCH CONFIGURATION: CAPTURED")
'''

r = subprocess.run(
    P + [
        "exec", "-i",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        matches[0], "/opt/venv/bin/python", "-B", "-"
    ],
    input=code,
    text=True,
    capture_output=True,
    timeout=30
)

print(r.stdout)
if r.stderr:
    print(r.stderr[-1500:])
print("EXIT CODE:", r.returncode)
print("CONTAINERS RESTARTED: NONE")
PY
