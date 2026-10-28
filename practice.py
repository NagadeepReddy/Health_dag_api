cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import re

base = Path("artifacts/v1.168-max/cta_max")

patterns = re.compile(
    r"session\.execute|\.execute\(|batch_size|batch_dim|"
    r"input_shape|output_shape|reshape\(|"
    r"zeros\(|ones\(|stack\(|concatenate\(|"
    r"TensorType|compile\(|inference|"
    r"\(1,\s*4,\s*256\)|2048",
    re.I
)

print("=== MAX INFERENCE BATCH COMPATIBILITY ===")

for p in sorted(base.rglob("*.py")):
    if "test" in p.name.lower() or "diag" in p.name.lower():
        continue
    lines = p.read_text(errors="replace").splitlines()
    matches = [
        (i, line) for i, line in enumerate(lines, 1)
        if patterns.search(line)
    ]
    if not matches:
        continue
    print(f"\nFILE: {p}")
    for i, line in matches[:35]:
        print(f"{i}: {line.strip()[:200]}")
    if len(matches) > 35:
        print(f"... {len(matches)-35} additional matches omitted")

print("\nINSPECTION COMPLETE")
print("DS CODE: UNCHANGED")
print("MAX MODEL: NOT STARTED")
print("WORKING NATIVE HTTP CODE: UNCHANGED")
PY
