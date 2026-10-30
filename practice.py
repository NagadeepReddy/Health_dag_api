python3 -B <<'PY'
from pathlib import Path
import ast, re

BASE = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)
REF = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "real_max_batch2_backend.py"
)

FILES = [
    ("ACTIVE NATIVE GRAPH",
     BASE / "grecbase_fusion_batch2_draft.py", 35, 90),
    ("ACTIVE AUXILIARY HELPER",
     BASE / "grecbase_aux_features_max.py", 1, 85),
    ("ACTIVE NLP HELPER",
     BASE / "nlp_bert_in_graph.py", 1, 165),
]

print("=== BATCH-2 ROOT-CAUSE SOURCE COMPARISON ===")

for title, path, start, end in FILES:
    print("\n===", title, "===")
    print("PATH:", path)

    if not path.is_file():
        print("MISSING")
        continue

    source = path.read_text()
    try:
        ast.parse(source)
        print("SYNTAX: PASS")
    except SyntaxError as e:
        print("SYNTAX ERROR:", e)
        continue

    lines = source.splitlines()

    if title == "ACTIVE NLP HELPER":
        patterns = (
            "return ", "def ", "ops.reshape",
            "ops.mean", "ops.max", "ops.concat"
        )
        selected = [
            (i, line) for i, line in enumerate(lines, 1)
            if any(p in line for p in patterns)
        ]
        for i, line in selected[:32]:
            print(f"{i}: {line}")
    else:
        for i in range(start, min(end, len(lines)) + 1):
            print(f"{i}: {lines[i-1]}")

print("\n=== PREVIOUSLY WORKING CPU BATCH BACKEND ===")
print("PATH:", REF)

if REF.is_file():
    lines = REF.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        if re.search(
            r"def |import |grecbase|graph|execute|batch|infer",
            line, re.I
        ):
            print(f"{i}: {line[:220]}")
else:
    print("Reference unavailable at known path")

print("\n=== CURRENT VERIFIED STATUS ===")
print("NATIVE CONTAINER: HEALTHY IN LAST CHECK")
print("CPU BATCH-2: PREVIOUSLY PASSED")
print("NATIVE HTTP BATCH-2: BLOCKED BY SHAPE")
print("FILES MODIFIED: NONE")
print("CONTAINERS RESTARTED: NONE")
print("NEXT: IDENTIFY FAULTY BRANCH BEFORE PATCH")
PY
