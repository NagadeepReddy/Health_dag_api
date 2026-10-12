python - <<'PY'
import ast
from pathlib import Path

original = Path(
    "artifacts/v1.168/utils/dependency-utils/models.py"
)
runner = Path(
    "artifacts/v1.168-max/cta_max/"
    "run_transformer_full_sequence.py"
)
block = Path(
    "artifacts/v1.168-max/cta_max/"
    "parallel_transformer_block_2layers.py"
)

def show(lines, start, end):
    for n in range(max(1, start), min(len(lines), end) + 1):
        print(f"{n}: {lines[n-1]}")

print("=== ORIGINAL vl_in HANDLING ===")
lines = original.read_text().splitlines()
tree = ast.parse(original.read_text())

count = 0
for cls in ast.walk(tree):
    if not isinstance(cls, ast.ClassDef):
        continue
    for fn in cls.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        if "vl_in" not in [a.arg for a in fn.args.args]:
            continue
        print(f"\n{cls.name}.{fn.name}")
        for n in range(fn.lineno, fn.end_lineno + 1):
            if "vl_in" in lines[n-1]:
                show(lines, n-4, n+5)
                count += 1
                if count >= 8:
                    break
        if count >= 8:
            break
    if count >= 8:
        break

print("\n=== EXISTING MAX POSITION GENERATION ===")
lines = runner.read_text().splitlines()
hits = [
    i+1 for i, line in enumerate(lines)
    if any(term in line for term in (
        "inv_freq", "position =", "pos =",
        "arange(", "angles ="
    ))
]
shown = set()
for hit in hits[:7]:
    for n in range(max(1, hit-3), min(len(lines), hit+5)+1):
        if n not in shown:
            print(f"{n}: {lines[n-1]}")
            shown.add(n)

print("\n=== MAX TRANSFORMER POSITION USAGE ===")
lines = block.read_text().splitlines()
hits = [
    i+1 for i, line in enumerate(lines)
    if "pos" in line.lower() or "rotary" in line.lower()
]
shown = set()
for hit in hits[:8]:
    for n in range(max(1, hit-2), min(len(lines), hit+3)+1):
        if n not in shown:
            print(f"{n}: {lines[n-1]}")
            shown.add(n)

print("\nREAD ONLY — NO FILES MODIFIED")
PY
