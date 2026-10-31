python3 -B - <<'PY'
from pathlib import Path

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
clean = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
terms = ("live_cta_pipeline_bridge", "cta_max_live_cta_pipeline_bridge")

print("=== BRIDGE FILE LOCATIONS ===")
for root in [repo / "artifacts/v1.168-max", clean / "artifacts/v1.168-max"]:
    for p in root.rglob("*live*bridge*.py"):
        if p.is_file():
            print("FOUND:", p)

print("\n=== STARTUP BRIDGE REFERENCES ===")
for root in [repo / "artifacts/v1.168-max/cta_native_batch2_release_candidate",
             clean / "artifacts/v1.168-max/cta_native_batch2_release_candidate"]:
    if not root.is_dir():
        continue
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            if any(t in line for t in terms):
                print(f"{p}:{n}: {line.strip()[:180]}")

print("\nORIGINAL FILES: UNCHANGED")
print("READ-ONLY CHECK COMPLETE")
PY
