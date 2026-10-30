python3 -B - <<'PY'
import json
import subprocess

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
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

root = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_batch2_release_candidate"
)
pkg = root / "maxserve_cta_extension"
launcher = pkg / "cta_native_launcher.py"

if not launcher.is_file():
    raise SystemExit("STOP: Staged launcher missing")

if not Path("/batch2/real_max_batch2_backend.py").is_file():
    raise SystemExit("STOP: Real MAX backend unavailable")

spec = importlib.util.find_spec(
    "maxserve_cta_extension.cta_native_launcher"
)

if spec is None or Path(spec.origin).resolve() != launcher.resolve():
    raise SystemExit("STOP: Staged launcher not selected")

print("STAGED LAUNCHER SELECTED: PASS", flush=True)

cmd = [
    sys.executable,
    "-B",
    "-m",
    "maxserve_cta_extension.cta_native_launcher",
    "--help"
]

result = subprocess.run(
    cmd,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    timeout=30
)

print("LAUNCHER HELP EXIT CODE:", result.returncode)

lines = result.stdout.splitlines()
for line in lines:
    if any(word in line.lower() for word in (
        "usage", "--port", "--model",
        "--host", "--device", "--help"
    )):
        print(line[:220])

if result.returncode != 0:
    print("LAUNCHER ERROR:", result.stdout[-1800:])
    raise SystemExit("STOP: Launcher CLI unavailable")

print("STAGED NATIVE LAUNCH PREFLIGHT: PASS")
print("SERVER STARTED: NO")
print("MAX EXECUTIONS: ZERO")
'''

env = (
    "PYTHONPATH="
    "/workspace/artifacts/v1.168-max/"
    "cta_native_batch2_release_candidate:"
    "/batch2:"
    "/workspace/artifacts/v1.168-max"
)

try:
    r = subprocess.run(
        P + [
            "exec", "-i", "-w", "/workspace",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", env,
            matches[0],
            "/opt/venv/bin/python", "-B", "-"
        ],
        input=code,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=45
    )
    print(r.stdout[-4000:])
    print("EXIT CODE:", r.returncode)
except subprocess.TimeoutExpired:
    print("STOP: Launcher preflight timed out")

print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
