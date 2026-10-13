python - <<'PY'
from pathlib import Path
import ast
import shutil

base = Path("artifacts/v1.168-max/cta_max")
p = base / "run_real_sanity_input_adapter.py"

old = 'add("page_wide", page_wide)'
new = 'add("page_wide", page_wide.reshape(1, 50, 1))'

source = p.read_text()

if old in source:
    updated = source.replace(old, new, 1)
    ast.parse(updated)
    backup = p.with_suffix(".py.before_page_wide_fix")
    if not backup.exists():
        shutil.copy2(p, backup)
    p.write_text(updated)
    print("PAGE_WIDE SHAPE FIXED: (1, 50, 1)")
elif new in source:
    print("PAGE_WIDE ALREADY FIXED")
else:
    raise SystemExit("STOP: Adapter changed unexpectedly")

print("\n=== SEQUENCE GRAPH INPUT CONTRACT ===")

found = False

for f in sorted(base.glob("*.py")):
    lines = f.read_text(errors="replace").splitlines()

    matches = [
        i for i, line in enumerate(lines)
        if (
            "def grecbase_max_sequence_max(" in line
            or "seq_inputs =" in line
            or "[1, 1, 50, 256]" in line
        )
    ]

    if not matches:
        continue

    found = True
    print("\nFILE:", f.name)

    shown = set()
    for i in matches:
        for j in range(max(0, i-3), min(len(lines), i+18)):
            if j not in shown:
                print(f"{j+1}: {lines[j]}")
                shown.add(j)

if not found:
    print("SEQUENCE DEFINITION NOT FOUND")

print("\nORIGINAL PYTORCH/DS CODE UNCHANGED")
PY
