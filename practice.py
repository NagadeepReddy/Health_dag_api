cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path

base = Path("/application1/cta_max_true_batch_dev_20261028")
roots = [
    Path("artifacts/v1.168-max"),
    base / "cta_max",
    base / "batch2_candidate/cta_max",
]

expected = "sibling_context_head_deep_embedding_0.weight.npy"

print("=== SIBLING WEIGHT SOURCE CHECK ===")

for root in roots:
    print("\nROOT:", root)
    if not root.is_dir():
        print("MISSING")
        continue

    matches = [
        p for p in root.rglob("*.npy")
        if "sibling" in p.name.lower()
        or "sibling" in str(p.parent).lower()
    ]

    print("SIBLING NPY FILES:", len(matches))
    for p in matches[:25]:
        print(p, p.stat().st_size, "bytes")

print("\n=== CODE EXPECTING SIBLING WEIGHTS ===")

candidate = base / "batch2_candidate/cta_max"

for p in sorted(candidate.glob("*.py")):
    lines = p.read_text().splitlines()
    positions = [
        i for i, line in enumerate(lines)
        if "sibling_context_weights" in line
        or expected in line
    ]
    for i in positions[:5]:
        print("\nFILE:", p.name)
        for j in range(max(0, i-3), min(len(lines), i+5)):
            print(f"{j+1}: {lines[j][:180]}")

print("\n=== RESULT ===")
print("WEIGHTS SEARCH: COMPLETE")
print("ORIGINAL MODEL: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
