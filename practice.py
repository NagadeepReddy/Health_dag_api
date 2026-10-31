python3 -B - <<'PY'
from pathlib import Path

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
checks = {
    "Original DS core": repo / "artifacts/v1.168/core-artifact",
    "Original DS utilities": repo / "artifacts/v1.168/utils/dependency-utils",
    "Native MAX model": repo / "artifacts/v1.168-max/cta_native_model",
    "Validated MAX code": repo / "artifacts/v1.168-max/cta_native_batch2_release_candidate",
}

for label, root in checks.items():
    print(f"\n=== {label} ===")
    if not root.is_dir():
        print("MISSING:", root)
        continue
    files = [p for p in root.rglob("*") if p.is_file()]
    print("PATH:", root)
    print("FILES:", len(files))
    print("TOTAL BYTES:", sum(p.stat().st_size for p in files))
    print("TOP-LEVEL ENTRIES:")
    for p in sorted(root.iterdir()):
        print(" ", p.name, "[DIR]" if p.is_dir() else "[FILE]")

print("\nREAD-ONLY CHECK COMPLETE")
PY
