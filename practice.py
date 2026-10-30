python3 - <<'PY'
import subprocess, json
from pathlib import Path

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-v2"

r = subprocess.run(
    pod + ["inspect", name],
    capture_output=True, text=True
)
assert r.returncode == 0, f"STOP: {r.stderr}"

data = json.loads(r.stdout)[0]
state = data.get("State", {})
config = data.get("HostConfig", {})

print("=== WORKER FAILURE CHECK ===")
print("CONTAINER:", state.get("Status"))
print("EXIT CODE:", state.get("ExitCode"))
print("OOM KILLED:", state.get("OOMKilled"))
print("MEMORY LIMIT MB:", config.get("Memory", 0)//1048576)

print("\n=== HOST MEMORY ===")
for line in Path("/proc/meminfo").read_text().splitlines():
    if line.startswith(("MemTotal:", "MemAvailable:")):
        print(line)

pid = state.get("Pid", 0)
if pid:
    cg = Path(f"/proc/{pid}/cgroup")
    if cg.exists():
        for line in cg.read_text().splitlines():
            if line.startswith("0::"):
                folder = Path("/sys/fs/cgroup") / line.split("::",1)[1].lstrip("/")
                for key in ("memory.current", "memory.max", "memory.events"):
                    f = folder / key
                    if f.exists():
                        print(f"\n{key}:\n{f.read_text().strip()}")

print("\n=== WORKER ERRORS ===")
logs = subprocess.run(
    pod + ["logs", "--tail", "250", name],
    capture_output=True, text=True
)
keys = ("OOM", "Killed", "MemoryError", "worker process",
        "Traceback", "ERROR", "CTA BATCH RETURNED",
        "CTA QUEUE SEND", "ExitCode")
matches = [
    x for x in (logs.stdout + logs.stderr).splitlines()
    if any(k in x for k in keys)
]
print("\n".join(matches[-25:]) or "NO MATCHING ERRORS")

print("\nORIGINAL DS: UNCHANGED")
print("NO FILES MODIFIED")
PY
