python - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

targets = {
    "parallel_transformer_block_2layers.py": [
        (1, 45), (65, 120)
    ],
    "grecbase_fusion_real_shapes_max.py": [
        (1, 42), (55, 82)
    ],
}

for name, ranges in targets.items():
    p = base / name
    assert p.is_file(), p
    lines = p.read_text().splitlines()
    print("\n===", name, "===")
    for first, last in ranges:
        for number in range(first, min(last, len(lines)) + 1):
            print(f"{number}: {lines[number-1]}")

print("\nREAD ONLY — NOTHING MODIFIED")
PY
