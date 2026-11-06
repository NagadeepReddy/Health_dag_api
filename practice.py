
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8")
repo = root / "rt-pzaas-sim-v1"

print("=== NEXT MODEL: PZAAS-SIM v1.50 ===")
print("SHARED MAX:", "PRESENT" if (root / "max_shared_infra").is_dir() else "MISSING")

if repo.is_dir():
    print("MODEL REPOSITORY: FOUND")
    print("PATH:", repo)
    for p in sorted(repo.iterdir()):
        if p.name in ("artifacts", "models", "src", "requirements.txt", "README.md"):
            print("MODEL COMPONENT:", p)
    print("NEXT: CONNECT PZAAS-SIM THROUGH EXISTING SHARED MAX")
else:
    print("MODEL REPOSITORY: NOT CLONED")
    print("NEXT: OBTAIN rt-pzaas-sim-v1 REPOSITORY")

print("SHARED INFRASTRUCTURE: UNCHANGED")
print("ORIGINAL MODELS: UNCHANGED")
print("NO CONTAINERS STARTED")
PY
