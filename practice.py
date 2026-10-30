python3 -B - <<'PY'
from pathlib import Path

base = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)

files = [
    base / "grecbase_fusion_batch2_draft.py",
    base / "grecbase_fusion_full_head_72_max.py",
]

for p in files:
    print("\n===== " + p.name + " =====")
    if not p.is_file():
        print("STOP: FILE MISSING")
        continue

    lines = p.read_text().splitlines()
    selected = set()

    for i, line in enumerate(lines):
        if any(word in line.lower() for word in (
            "sibling", "pool", "valid_length", "valid_len"
        )):
            selected.update(range(
                max(0, i - 6),
                min(len(lines), i + 9)
            ))

    if "batch2_draft" in p.name:
        selected.update(range(
            max(0, 44),
            min(len(lines), 72)
        ))

    for i in sorted(selected):
        print(f"{i+1}: {lines[i]}")

print("\nREAD ONLY: PASS")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
