
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8")
shared = root / "max_shared_infra"

print("=== CTA / BPLAN SHARED LAUNCH CONFIGURATION ===")

for name in ("CTA", "BPLAN"):
    print(f"\n=== {name} ===")

    configs = [
        p for p in shared.rglob("model.env")
        if name.lower() in str(p).lower()
    ]

    print("SHARED CONFIGURATIONS:")
    if configs:
        for p in configs:
            print(p)
    else:
        print("NONE FOUND - needs isolated shared package configuration")

    print("EXISTING SHARED INTEGRATION:")
    dirs = [
        p for p in (shared / "isolated").glob("*")
        if name.lower() in p.name.lower()
    ] if (shared / "isolated").is_dir() else []

    for p in dirs:
        print(p)

    if not dirs:
        print("NONE FOUND")

print("\n=== ORIGINAL HANDOFFS ===")
for name, path in {
    "CTA": Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"),
    "BPLAN": Path("/application1/BPLAN_MAX_TEAM_HANDOFF_20261102"),
}.items():
    print(name, "PRESENT" if path.is_dir() else "MISSING")

print("\nORIGINAL FILES: UNCHANGED")
print("CONTAINERS STARTED: NONE")
print("NEXT: COMPLETE CTA/BPLAN SHARED CONFIGS, THEN CONCURRENT HTTP")
PY
