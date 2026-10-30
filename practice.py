python3 -B - <<'PY'
import subprocess
import json

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

r = subprocess.run(
    P + ["ps", "-a", "--format", "json"],
    capture_output=True, text=True
)

if r.returncode:
    raise SystemExit(r.stderr)

containers = json.loads(r.stdout)
ids = [
    c.get("Id") or c.get("ID")
    for c in containers
]
ids = [x for x in ids if x]

if not ids:
    raise SystemExit("STOP: No existing containers found")

r = subprocess.run(
    P + ["inspect", *ids],
    capture_output=True, text=True
)

if r.returncode:
    raise SystemExit(r.stderr)

details = json.loads(r.stdout)

print("=== PREVIOUS CONTAINER ===")

for c in details:
    cid = c.get("Id", "")
    state = c.get("State", {})
    if cid.startswith("a176e284b50a"):
        print("ID:", cid[:12])
        print("STATUS:", state.get("Status"))
        print("EXIT CODE:", state.get("ExitCode"))
        print("OOM KILLED:", state.get("OOMKilled"))
        print("STATE ERROR:", state.get("Error"))

print("\n=== RUNNING BATCH-2 CANDIDATES ===")

found = 0

for c in details:
    state = c.get("State", {})
    if not state.get("Running"):
        continue

    destinations = {
        m.get("Destination", "")
        for m in c.get("Mounts", [])
    }

    workspace = "/workspace" in destinations
    batch2 = "/batch2" in destinations

    if not workspace:
        continue

    found += 1

    print("\nID:", c.get("Id", "")[:12])
    print("NAME:", c.get("Name"))
    print("IMAGE:", c.get("Config", {}).get("Image"))
    print("WORKSPACE MOUNT:", workspace)
    print("BATCH-2 MOUNT:", batch2)

print("\nRUNNING WORKSPACE CANDIDATES:", found)
print("NO CONTAINERS STARTED OR RESTARTED")
print("NO MODEL EXECUTIONS")
print("ORIGINAL DS/MAX UNCHANGED")
PY
