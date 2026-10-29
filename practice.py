cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path

roots = [
    Path("/application1/cta_max_native_release_candidate_20261028"),
    Path("artifacts/v1.168-max/maxserve_cta_extension"),
]

for name in ("cta_pipeline_model.py", "cta_architecture_registration.py"):
    files = [r / name for r in roots if (r / name).is_file()]
    print(f"\n=== {name} ===")
    if not files:
        print("MISSING")
        continue

    p = files[0]
    print("SOURCE:", p)
    lines = p.read_text().splitlines()

    for i, line in enumerate(lines, 1):
        if any(term in line.lower() for term in (
            "weight", "load", "modelconfig", "pipeline",
            "encoding", "architecture", "register"
        )):
            lo, hi = max(0, i-3), min(len(lines), i+4)
            for j in range(lo, hi):
                print(f"{j+1}: {lines[j][:180]}")

print("\nMODEL STARTED: NO")
print("FILES MODIFIED: NONE")
PY
