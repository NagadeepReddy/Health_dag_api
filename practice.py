python3 - <<'PY'
import subprocess, json, re

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-v2"

def run(args):
    return subprocess.run(
        args, capture_output=True, text=True, timeout=30
    )

r = run(pod + ["inspect", name])
assert r.returncode == 0, r.stderr
info = json.loads(r.stdout)[0]
s = info["State"]

print("=== CURRENT WORKER STATE ===")
for key in ("Status", "Pid", "ExitCode", "OOMKilled", "StartedAt"):
    print(key, ":", s.get(key))

r = run(pod + [
    "stats", "--no-stream", "--format",
    "{{.CPUPerc}} CPU | {{.MemUsage}} MEMORY",
    name
])
print("RESOURCE USAGE:", r.stdout.strip() or r.stderr.strip())

r = run(pod + [
    "logs", "--timestamps", "--tail", "700", name
])

lines = (r.stdout + r.stderr).splitlines()
pattern = re.compile(
    r"CTA |BATCH|COMPIL|GRAPH|CHECKPOINT|EXECUTING|"
    r"MODEL LOAD|worker process|ERROR|Traceback|"
    r"ModuleNotFoundError|ImportError|OOM|Killed|"
    r"predict HTTP|Exception|START|STOP",
    re.I
)
matches = [x for x in lines if pattern.search(x)]

print("\n=== WORKER EXECUTION STAGES ===")
print("\n".join(matches[-65:]) or "NO STAGE LOGS")

print("\n=== MOST RECENT RAW LOGS ===")
print("\n".join(lines[-25:]) or "NO LOG OUTPUT")

print("\nNO FILES MODIFIED")
print("ORIGINAL MAX: UNCHANGED")
PY
