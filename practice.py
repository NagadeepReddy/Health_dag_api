python - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
found = 0

for p in sorted(base.rglob("*.py")):
    lines = p.read_text().splitlines()
    source = "\n".join(lines)

    if not (
        "AttPoolingBlockMAX" in source
        or "fused_attn_ff_proj" in source
    ):
        continue

    if not (
        "weights_registry" in source
        or "WeightsRegistry" in source
    ):
        continue

    print(f"\n===== {p.name} =====")
    indices = [
        i for i, line in enumerate(lines)
        if any(term in line for term in (
            "weights_registry",
            "WeightsRegistry",
            "weights =",
            "session.load(",
            "fused_attn_ff_proj",
        ))
    ]

    shown = set()
    for i in indices[:8]:
        for j in range(max(0, i-4), min(len(lines), i+6)):
            if j not in shown:
                print(f"{j+1}: {lines[j]}")
                shown.add(j)

    found += 1
    if found >= 3:
        break

print("\nMATCHING FILES:", found)
print("READ ONLY — NO FILES MODIFIED")
PY
