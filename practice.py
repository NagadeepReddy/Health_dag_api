python3 -B - <<'PY'
import json, subprocess, re
from pathlib import Path

P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]

ids = subprocess.check_output(P + ["ps", "-q"], text=True).split()
if not ids:
    raise SystemExit("STOP: No running containers")

items = json.loads(subprocess.check_output(
    P + ["inspect"] + ids, text=True
))

def listening_ports(pid):
    ports = set()
    if not isinstance(pid, int) or pid <= 0:
        return []
    for name in ("tcp", "tcp6"):
        f = Path(f"/proc/{pid}/net/{name}")
        try:
            lines = f.read_text().splitlines()[1:]
            for line in lines:
                fields = line.split()
                if len(fields) > 3 and fields[3] == "0A":
                    ports.add(int(fields[1].split(":")[1], 16))
        except (OSError, ValueError, IndexError):
            continue
    return sorted(ports)

print("MAX SERVE RUNTIME INVENTORY")
found = 0

for item in items:
    cid = item["Id"]
    name = item.get("Name", "")
    image = item.get("ImageName") or item.get("Config", {}).get("Image", "")
    mounts = item.get("Mounts") or []

    relevant = (
        "max" in image.lower()
        or "cta" in image.lower()
        or any("CTA_MAX_TRUE_BATCH2_DEV_20261029" in m.get("Source", "")
               for m in mounts)
    )
    if not relevant:
        continue

    found += 1
    stage_mount = any(
        "CTA_MAX_TRUE_BATCH2_DEV_20261029" in m.get("Source", "")
        and m.get("Destination") == "/batch2"
        for m in mounts
    )

    pid = (item.get("State") or {}).get("Pid")
    ports = listening_ports(pid)
    process = subprocess.run(
        P + ["top", cid, "args"],
        text=True, capture_output=True, timeout=10
    )
    running = process.stdout.lower() if process.returncode == 0 else ""
    serve = bool(re.search(
        r"cta_native_launcher|max[._ -]*serve|uvicorn",
        running
    ))

    print(f"\nCONTAINER: {cid[:12]} {name}")
    print("IMAGE:", image)
    print("NETWORK:", (item.get("HostConfig") or {}).get("NetworkMode"))
    print("BATCH-2 MOUNT:", "YES" if stage_mount else "NO")
    print("MAX SERVE PROCESS:", "DETECTED" if serve else "NOT CONFIRMED")
    print("LISTENING TCP PORTS:", ports)
    print("PORT 8000 LISTENING:", 8000 in ports)

print("\nRELEVANT CONTAINERS:", found)
print("RUNTIME INSPECTION: COMPLETE")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MAX EXECUTIONS: ZERO")
PY
