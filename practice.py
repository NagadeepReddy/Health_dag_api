cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path

root = Path("artifacts/v1.472-max/pzaas_max")
terms = (
    "np.load(", ".npy", "2048", "10819",
    "10727", "256", "cta_max",
    "weight_dir", "weights_dir",
    "TensorType(", "graph.add_input"
)

for p in sorted(root.glob("*.py")):
    lines = p.read_text().splitlines()
    hits = [
        (i, line.strip())
        for i, line in enumerate(lines, 1)
        if any(term in line for term in terms)
    ]
    print(f"\n=== {p.name} | {len(hits)} matches ===")
    for i, line in hits[:15]:
        print(f"{i}: {line[:160]}")

print("\nPZAAS GRAPH DIMENSION/WEIGHT AUDIT: COMPLETE")
print("NO FILES MODIFIED")
PY
