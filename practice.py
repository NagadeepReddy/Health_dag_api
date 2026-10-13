python - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
names = [
    "parallel_transformer_block.py",
    "parallel_transformer_graph_full_sequence.py",
    "grecbase_fusion_order_correct_max.py",
]

for name in names:
    p = base / name
    print(f"\n=== {name} ===")
    if not p.exists():
        print("NOT FOUND")
        continue

    lines = p.read_text().splitlines()
    hits = [
        i for i, line in enumerate(lines)
        if (
            "pos" in line.lower()
            or "rotary" in line.lower()
            or "inv_freq" in line
        ) and not line.strip().startswith("#")
    ]

    shown = set()
    for i in hits[:18]:
        for j in range(max(0, i-2), min(len(lines), i+3)):
            if j not in shown:
                print(f"{j+1}: {lines[j]}")
                shown.add(j)

print("\nREAD ONLY — NO FILES CHANGED")
PY
