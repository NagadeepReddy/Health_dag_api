python3 -B - <<'PY'
from pathlib import Path
import subprocess, json, shutil

root = Path("/application1")
repo = root / "sajjna8/rt-pzaas-cta-offers-v1"
dev = root / "CTA_MAX_TRUE_BATCH2_DEV_20261029"
stage = dev / "native_batch2_release_candidate/maxserve_cta_extension"

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

required = [
    stage / "cta_worker_adapter.py",
    stage / "cta_native_scheduler.py",
    stage / "cta_scheduler_factory.py",
    stage / "cta_native_launcher.py",
    dev / "real_max_batch2_backend.py"
]

for p in required:
    if not p.is_file():
        raise SystemExit("STOP: Required file missing: " + str(p))

print("STAGED NATIVE BATCH-2: PRESENT", flush=True)

ram = int(next(
    line.split()[1]
    for line in Path("/proc/meminfo").read_text().splitlines()
    if line.startswith("MemAvailable:")
)) // 1024

disk = shutil.disk_usage(dev).free // (1024 * 1024)

print("AVAILABLE RAM MB:", ram)
print("WORKSPACE FREE MB:", disk)

r = subprocess.run(
    P + ["ps", "-q"],
    capture_output=True, text=True, check=True
)

ids = r.stdout.split()
print("RUNNING CONTAINERS:", len(ids))

found = 0

for cid in ids:
    r = subprocess.run(
        P + ["inspect", cid],
        capture_output=True, text=True, check=True
    )
    info = json.loads(r.stdout)[0]
    mounts = info.get("Mounts", [])
    image = info.get("ImageName") or info.get("Config", {}).get("Image", "")

    relevant = [
        m for m in mounts
        if str(repo) in m.get("Source", "")
        or str(dev) in m.get("Source", "")
    ]

    if not relevant and not any(
        word in image.lower() for word in ("max", "cta")
    ):
        continue

    found += 1
    print("\nCONTAINER:", cid[:12])
    print("IMAGE:", image)
    print("NETWORK:", info.get("HostConfig", {}).get("NetworkMode"))
    print("WORKDIR:", info.get("Config", {}).get("WorkingDir"))

    for m in mounts:
        src = m.get("Source", "")
        if str(repo) in src or str(dev) in src:
            print(
                "MOUNT:",
                src,
                "=>",
                m.get("Destination"),
                "RW:", m.get("RW")
            )

    ports = info.get("NetworkSettings", {}).get("Ports") or {}
    print("PORTS:", json.dumps(ports))

print("\nRELEVANT RUNNING CONTAINERS:", found)

if ram < 12000:
    print("FINAL TEST RESOURCE STATUS: LOW MEMORY")
else:
    print("FINAL TEST RESOURCE STATUS: MEMORY AVAILABLE")

print("RUNTIME CONFIGURATION CHECK: COMPLETE")
print("ORIGINAL DS/MAX: UNCHANGED")
print("WORKING RELEASE: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MAX EXECUTIONS: ZERO")
PY
