python - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for name, start, end in [
    ("parallel_transformer_block_2layers.py", 105, 150),
    ("grecbase_fusion_real_shapes_max.py", 18, 48),
]:
    p = base / name
    assert p.is_file(), p
    print(f"\n=== {name} ===")
    lines = p.read_text().splitlines()
    for i in range(start, min(end, len(lines)) + 1):
        print(f"{i}: {lines[i-1]}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
