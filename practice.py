python - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
matches = []

for p in sorted(base.rglob("*.py")):
    if p.name.startswith("grecbase_fusion"):
        continue

    lines = p.read_text().splitlines()
    source = "\n".join(lines)

    if (
        "sequence_transformer.page_embedding" in source
        and (
            "weights_registry" in source
            or "WeightData" in source
        )
    ):
        matches.append((p, lines))

print("SEQUENCE WEIGHT LOADER FILES:", len(matches))

for p, lines in matches[:3]:
    print("\nFILE:", p)

    locations = [
        i for i, line in enumerate(lines)
        if any(term in line for term in (
            "sequence_transformer.page_embedding",
            "weight_files =",
            "weights =",
            "WeightData",
            "weights_registry=",
            "for name, path in",
        ))
    ]

    shown = set()
    for i in locations[:10]:
        for j in range(
            max(0, i-3),
            min(len(lines), i+6)
        ):
            if j not in shown:
                print(f"{j+1}: {lines[j]}")
                shown.add(j)

print("\nREAD ONLY — NO FILES MODIFIED")
PY
