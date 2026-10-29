cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 - <<'PY'
from pathlib import Path
import tarfile

archive = Path(
    "/application1/CTA_MAX_NATIVE_CONCURRENT2_PASS_20261029.tar.gz"
)
stage = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2_live_stage"
)

assert archive.is_file(), "STOP: Successful native archive missing"
assert stage.is_dir(), "STOP: Batch-2 stage missing"

print("=== PREVIOUSLY SUCCESSFUL NATIVE ARCHIVE ===")

with tarfile.open(archive, "r:gz") as tar:
    candidates = [
        m for m in tar.getmembers()
        if m.isfile()
        and m.size < 500000
        and m.name.endswith((".py", ".sh", ".log", ".txt"))
        and any(k in m.name.lower() for k in (
            "launcher", "concurrent", "http",
            "startup", "native", "serve"
        ))
    ]

    print("MATCHING FILES:", len(candidates))
    for m in candidates[:35]:
        print("FILE:", m.name)

    print("\n=== VERIFIED STARTUP REFERENCES ===")
    terms = (
        "podman run", "MAX_SERVE_API_TYPES",
        "API_TYPES=", "Server ready",
        "HTTP 200", "CTA PREDICT_RAW",
        "--model-path", "--weight-path",
        "--network", "--memory", "--cpus",
    )

    selected = sorted(
        candidates,
        key=lambda m: (
            "concurrent" not in m.name.lower(),
            "launcher" not in m.name.lower(),
            m.name
        )
    )

    for m in selected[:15]:
        f = tar.extractfile(m)
        if f is None:
            continue
        lines = f.read(250000).decode(
            errors="replace"
        ).splitlines()

        found = [
            (i, line.strip())
            for i, line in enumerate(lines, 1)
            if any(t.lower() in line.lower() for t in terms)
        ]

        if found:
            print("\nFILE:", m.name)
            for i, line in found[:15]:
                print(f"{i}: {line[:220]}")

print("\n=== CURRENT BATCH-2 STAGE ===")
for name in (
    "cta_native_launcher.py",
    "cta_router.py",
    "cta_worker_adapter.py",
    "cta_native_scheduler.py",
    "cta_scheduler_factory.py",
):
    p = stage / name
    print(name, "PRESENT" if p.is_file() else "MISSING")

print("\nSUCCESSFUL ARCHIVE INSPECTION: COMPLETE")
print("ORIGINAL DS: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
print("NO SERVER STARTED")
print("NO FILES MODIFIED")
PY
