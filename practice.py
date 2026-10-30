python3 -B <<'PY'
from pathlib import Path
import re

root = Path(
    "/application1/cta_max_true_batch_dev_20261028"
    "/batch2_candidate/cta_max"
)

files = [
    root / "grecbase_fusion_full_head_72_max.py",
    root / "grecbase_fusion_batch2_draft.py",
    root / "grecbase_fusion_order_correct_max.py",
]

files += sorted(root.glob("*sequence*.py"))[:4]

print("=== SEQUENCE BRANCH TARGETED CHECK ===")

for p in dict.fromkeys(files):
    if not p.is_file():
        continue

    lines = p.read_text().splitlines()
    matches = [
        i for i, line in enumerate(lines)
        if re.search(r"\bseq\b|sequence|pool", line, re.I)
    ]

    if not matches:
        continue

    print("\nFILE:", p.name)
    printed = set()

    for i in matches[:12]:
        for j in range(max(0, i-2), min(len(lines), i+4)):
            if j not in printed:
                print(f"{j+1}: {lines[j]}")
                printed.add(j)

print("\nORIGINAL DS/MAX: UNCHANGED")
print("FILES MODIFIED: NONE")
print("CONTAINERS RESTARTED: NONE")
print("NEXT: VERIFY SEQUENCE POOLING BEFORE PATCH")
PY
