cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path

repo = Path.cwd()
base = Path("/application1/cta_max_true_batch_dev_20261028")

roots = [
    repo / "artifacts/v1.168-max/cta_max",
    base / "cta_max",
    base / "batch2_candidate/cta_max",
]

print("=== ROTARY WEIGHT FILES ===")
for root in roots:
    weight_dir = root / "grecbase_integration_weights"
    print("DIRECTORY:", weight_dir)
    print("EXISTS:", weight_dir.is_dir())
    if weight_dir.is_dir():
        for p in sorted(weight_dir.glob("*rotary*")):
            print("WEIGHT:", p.name, "BYTES:", p.stat().st_size)

print("\n=== ERROR SOURCE AND WEIGHT LOOKUP ===")
for root in roots:
    if not root.is_dir():
        continue
    for p in sorted(root.glob("*.py")):
        lines = p.read_text(errors="replace").splitlines()
        matches = [
            i for i, line in enumerate(lines)
            if "No exported 256-d rotary" in line
            or "rotary_emb.inv_freq" in line
        ]
        for i in matches:
            print("\nFILE:", p)
            for j in range(max(0, i-5), min(len(lines), i+5)):
                print(f"{j+1}: {lines[j]}")

print("\nCHECK COMPLETE — NO FILES MODIFIED")
print("MAX NOT STARTED")
PY
