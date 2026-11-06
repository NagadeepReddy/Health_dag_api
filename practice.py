
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/max_shared_infra")

print("=== THREE-MODEL SHARED MAX LAUNCH CONFIGURATION ===")

for folder in (root / "bin", root / "isolated"):
    if not folder.is_dir():
        print("NOT FOUND:", folder)
        continue

    for p in sorted(folder.rglob("*.sh")):
        if "run" not in p.name and "launch" not in p.name:
            continue
        print("\n=== SCRIPT:", p, "===")
        lines = p.read_text(errors="replace").splitlines()
        for i, line in enumerate(lines[:140], 1):
            print(f"{i}: {line}")

print("\n=== VERIFIED MODEL PACKAGES ===")
for name, path in {
    "CTA": Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030"),
    "BPLAN": Path("/application1/BPLAN_MAX_TEAM_HANDOFF_20261102"),
    "PZAAS": Path("/application1/sajjna8/PZAAS_MAX_CLEAN_HANDOFF_20261106"),
}.items():
    print(name, path, "PRESENT" if path.is_dir() else "NOT FOUND")

print("\nNO FILES MODIFIED")
print("NO CONTAINERS STARTED")
print("NEXT: START ALL THREE CONCURRENTLY AND VERIFY HTTP 200")
PY
