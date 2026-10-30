PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess, json, urllib.request
from datetime import datetime

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-10g"

def run(args):
    return subprocess.run(
        args, capture_output=True, text=True, timeout=45
    )

def health(port):
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=5
        ) as r:
            return r.status
    except Exception:
        return "UNAVAILABLE"

print("=== CURRENT ISOLATED STATE ===")

r = run(pod + ["inspect", name])
assert r.returncode == 0, "STOP: Container missing"

info = json.loads(r.stdout)[0]
state = info["State"]

for key in (
    "Status", "Running", "ExitCode",
    "OOMKilled", "StartedAt", "FinishedAt"
):
    print(f"{key}: {state.get(key)}")

print("MEMORY LIMIT GB:",
      round(info["HostConfig"]["Memory"] / 1024**3, 2))

print("ORIGINAL MAX 8765:", health(8765))
print("ISOLATED MAX 8766:", health(8766))

print("\n=== CURRENT STARTUP LOGS ===")

started = state.get("StartedAt")
args = pod + ["logs", "--tail", "650"]

if started and not started.startswith("0001-"):
    args += ["--since", started]

args.append(name)
r = run(args)

logs = (r.stdout + "\n" + r.stderr).splitlines()

keywords = (
    "Traceback", "Error", "ERROR", "Exception",
    "STOP:", "OOM", "Killed", "failed",
    "ModuleNotFound", "ImportError",
    "BATCH-2", "GRAPH", "worker",
    "Application startup complete"
)

matches = [
    (i, line) for i, line in enumerate(logs)
    if any(k.lower() in line.lower() for k in keywords)
]

print("\n=== LATEST RELEVANT EVENTS ===")
for _, line in matches[-35:]:
    print(line[:450])

print("\n=== LATEST ERROR CONTEXT ===")
errors = [
    i for i, line in enumerate(logs)
    if any(k in line for k in (
        "Traceback (most recent",
        "ERROR:", "Error:", "Exception:",
        "STOP:", "OOM", "Killed"
    ))
]

if errors:
    i = errors[-1]
    for line in logs[max(0, i-8):min(len(logs), i+35)]:
        print(line[:450])
else:
    for line in logs[-25:]:
        print(line[:450])

print("\nORIGINAL DS: UNCHANGED")
print("CONTAINERS: NOT RESTARTED")
print("FILES MODIFIED: NONE")
PY
