python3 -B <<'PY'
from pathlib import Path
import ast

DEV = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
ORIG = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")

print("=== CONTEXT BRANCH ROOT-CAUSE CHECK ===")

for label, root in [
    ("ISOLATED BATCH-2", DEV),
    ("PREVIOUS VALIDATED MAX", ORIG),
]:
    print("\n===", label, "===")
    for name in [
        "main_context_max.py",
        "grecbase_fusion_full_head_72_max.py",
        "grecbase_fusion_batch2_draft.py",
    ]:
        p = root / name
        if not p.is_file():
            continue

        print("\nFILE:", p)
        lines = p.read_text().splitlines()

        for i, line in enumerate(lines):
            if (
                "def main_context_forward" in line
                or "main_context_forward(" in line
                or "context, deep_extract =" in line
                or "ops.reshape(x, [2, 1, 256])" in line
            ):
                a = max(0, i - 5)
                b = min(len(lines), i + 12)
                for j in range(a, b):
                    print(f"{j+1}: {lines[j]}")

        if name == "main_context_max.py":
            print("\nCONTEXT FUNCTION RETURN / POOLING:")
            for i, line in enumerate(lines):
                if any(x in line for x in (
                    "return ", "ops.mean(", "ops.max(",
                    "ops.sum(", "ops.concat(", "ops.reshape("
                )):
                    print(f"{i+1}: {line}")

print("\n=== RESULT ===")
print("FAULT: 3x128 context candidate versus 256-wide fusion")
print("PREVIOUSLY PASSED CPU BATCH-2: PRESERVED")
print("ORIGINAL DS/MAX: UNCHANGED")
print("FILES MODIFIED: NONE")
print("CONTAINERS RESTARTED: NONE")
print("NEXT: USE VERIFIED CONTEXT AGGREGATION, NOT ARBITRARY RESHAPE")
PY
