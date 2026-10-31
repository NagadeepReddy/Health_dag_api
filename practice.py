python3 -B - <<'PY'
from pathlib import Path

roots = {
    "ORIGINAL": Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max"),
    "CLEAN": Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max"),
}

for label, root in roots.items():
    print(f"\n=== {label} ROTARY WEIGHTS ===")
    files = sorted(root.rglob("*inv_freq*.npy"))
    if not files:
        print("MISSING")
    for p in files:
        with p.open("rb") as f:
            valid = f.read(6) == b"\x93NUMPY"
        print(
            "VALID_NPY=" + str(valid),
            "SIZE=" + str(p.stat().st_size),
            "PATH=" + str(p.relative_to(root))
        )

print("\nREAD-ONLY CHECK COMPLETE")
PY
