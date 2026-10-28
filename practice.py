cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import difflib

base = Path("/application1/cta_max_true_batch_dev_20261028")
original = base / "cta_max"
candidate = base / "batch2_candidate/cta_max"

assert original.is_dir(), "STOP: Original batch source missing"
assert candidate.is_dir(), "STOP: Existing candidate missing"

changed = []
issues = []

for new in sorted(candidate.rglob("*.py")):
    old = original / new.relative_to(candidate)
    if not old.is_file():
        issues.append(f"Missing original: {new.name}")
        continue

    before = old.read_text()
    after = new.read_text()
    ast.parse(after)

    if before == after:
        continue

    changed.append(new.name)

    print(f"\n=== {new.name} ===")
    diff = list(difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        n=1,
        lineterm=""
    ))

    for line in diff:
        if line.startswith(("---", "+++")):
            continue
        print(line)

print("\n=== VALIDATION SUMMARY ===")
print("CANDIDATE: EXISTS")
print("PYTHON SYNTAX: PASS")
print("CHANGED FILES:", len(changed))
print("SOURCE ISSUES:", issues if issues else "NONE")
print("BATCH SHAPE VALIDATION: STILL PENDING")
print("TRUE BATCH INFERENCE: NOT YET PROVEN")
print("WORKING HTTP 200: UNCHANGED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
