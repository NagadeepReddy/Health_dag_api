cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
from datetime import datetime
import re, shutil, ast, sys

p = Path("artifacts/v1.472-max/pzaas_max/grecbase_fusion_full_head_72_max.py")

print("=== PZAAS TRAINED DEPTH ALIGNMENT ===")

if not p.is_file():
    sys.exit("BLOCKED: MAX fusion file missing")

original = p.read_text()
updated = original

if not re.search(r'\bblock2\s*=', original):
    if (re.search(r'\bblock1\s*=', original)
        and not re.search(r'\bblock[2-5]\s*=', original)
        and re.search(r'postprocess\(sx2\)', original)):
        print("MAX DEPTH: ALREADY TWO")
        sys.exit(0)
    sys.exit("BLOCKED: Unexpected graph structure")

patterns = []

for i in range(2, 6):
    patterns.append((
        rf'(?m)^[ \t]*block{i}\s*=\s*ParallelTransformerBlockMAX\([^\n]*layer_idx\s*=\s*{i}\)[ \t]*\n',
        '',
        f"REMOVE EXTRA BLOCK {i}"
    ))

for i in range(3, 7):
    patterns.append((
        rf'(?m)^[ \t]*sx{i}\s*=\s*sx{i-1}\s*\+\s*block{i-1}\([^\n]*\)[ \t]*\n',
        '',
        f"REMOVE EXTRA EXECUTION {i}"
    ))

patterns.append((
    r'postprocess\(sx6\)',
    'postprocess(sx2)',
    "USE TRAINED LAYER 1 OUTPUT"
))

for pattern, replacement, label in patterns:
    updated, count = re.subn(pattern, replacement, updated)
    if count != 1:
        sys.exit(f"BLOCKED: {label}; matches={count}")
    print(label + ": PASS")

if re.search(r'\b(?:block[2-5]|sx[3-6])\b', updated):
    sys.exit("BLOCKED: Extra layer references remain")

try:
    ast.parse(updated)
    compile(updated, str(p), "exec")
except Exception as e:
    sys.exit(f"BLOCKED: Syntax validation: {e}")

backup = p.with_name(
    p.name + ".backup_" +
    datetime.now().strftime("%Y%m%d_%H%M%S")
)

shutil.copy2(p, backup)

try:
    p.write_text(updated)
    assert p.read_text() == updated
except Exception:
    shutil.copy2(backup, p)
    raise

print("\n=== RESULTS ===")
print("TRAINED DEPTH: 2")
print("MAX GRAPH DEPTH: 2")
print("PYTHON SYNTAX: PASS")
print("SOURCE BACKUP: SAVED")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: REAL MAX NUMERICAL PARITY")
PY
