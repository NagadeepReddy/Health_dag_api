cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path

base = Path("/application1/cta_max_true_batch_dev_20261028")
roots = [
    base / "cta_max",
    base / "batch2_candidate/cta_max",
]

terms = (
    "No exported 256-d",
    "rotary",
    "inv_freq",
    "weights_registry",
    "grecbase_integration_weights",
)

for root in roots:
    print("\n=== SOURCE:", root, "===")
    if not root.is_dir():
        print("MISSING")
        continue

    for name in (
        "run_live_max_inference.py",
        "run_batch2_live_max_inference.py",
        "grecbase_fusion_full_head_72_max.py",
        "grecbase_fusion_order_correct_max.py",
    ):
        p = root / name
        if not p.is_file():
            continue
        lines = p.read_text().splitlines()
        matches = [
            i for i, line in enumerate(lines)
            if any(term.lower() in line.lower() for term in terms)
        ]
        if matches:
            print("\nFILE:", name)
            shown = set()
            for i in matches[:10]:
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    if j not in shown:
                        print(f"{j+1}: {lines[j][:180]}")
                        shown.add(j)

    for folder in root.rglob("grecbase_integration_weights"):
        if folder.is_dir():
            print("\nEXPORTED ROTARY FILES:")
            for p in sorted(folder.glob("*rotary*")):
                print(p.name, p.stat().st_size, "bytes")

print("\nWORKING MODEL: UNCHANGED")
print("BATCH MODEL: NOT STARTED")
print("DS CODE: UNCHANGED")
PY
