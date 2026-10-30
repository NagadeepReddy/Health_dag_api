PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess, json, os

pod = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-10g"

r = subprocess.run(
    pod + ["inspect", name],
    capture_output=True, text=True
)

if r.returncode:
    print("INSPECT FAILED:", r.stderr)
    raise SystemExit(1)

info = json.loads(r.stdout)[0]
state = info.get("State", {})
graph = info.get("GraphDriver", {}).get("Data", {})

print("=== ISOLATED CONTAINER ===")
print("STATUS:", state.get("Status"))
print("PID:", state.get("Pid"))
print("STATE ERROR:", state.get("Error"))
print("STORAGE DRIVER:", info.get("GraphDriver", {}).get("Name"))

print("\n=== OVERLAY PATH CHECK ===")
for key in ("MergedDir", "UpperDir", "WorkDir"):
    path = graph.get(key, "")
    print(key, ":", path or "NOT REPORTED")
    if path:
        print("  DIRECTORY EXISTS:", os.path.isdir(path))
        print("  ETC EXISTS:", os.path.isdir(os.path.join(path, "etc")))
        print("  PASSWD EXISTS:", os.path.isfile(os.path.join(path, "etc/passwd")))

print("\n=== OVERLAY MOUNT STATUS ===")
merged = graph.get("MergedDir", "")
mounted = False

if merged:
    with open("/proc/self/mountinfo") as f:
        mounted = any(
            line.split(" - ")[0].split()[4] == merged
            for line in f
        )

print("OVERLAY MOUNTED:", mounted)

print("\nORIGINAL MAX: NOT TOUCHED")
print("ORIGINAL DS: UNCHANGED")
print("FILES MODIFIED: NONE")
print("CONTAINERS RESTARTED: NONE")
PY
