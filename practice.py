python - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
terms = (
    "WeightData", "weights_registry", "weight_files",
    "page_embedding", "SEQUENCE WEIGHTS REGISTERED",
    "TOTAL REGISTERED WEIGHTS"
)

print("=== EXISTING WEIGHT REGISTRATION ===")
for p in sorted(base.glob("*.py")):
    lines = p.read_text().splitlines()
    matches = [i for i, line in enumerate(lines)
               if any(t in line for t in terms)]
    if not matches:
        continue
    print("\nFILE:", p.name)
    shown = set()
    for i in matches[:12]:
        for j in range(max(0, i-3), min(len(lines), i+4)):
            if j not in shown:
                print(f"{j+1}: {lines[j]}")
                shown.add(j)

print("\n=== CURRENT FUSION GRAPH SETUP ===")
p = base / "grecbase_fusion_real_shapes_max.py"
assert p.is_file()
lines = p.read_text().splitlines()
for i, line in enumerate(lines[:22], 1):
    print(f"{i}: {line}")

print("\nREAD ONLY — NOTHING MODIFIED")
PY
