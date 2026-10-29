python3 - <<'PY'
from pathlib import Path
import ast

root = Path("/application1")
dev = root / "CTA_MAX_TRUE_BATCH2_DEV_20261029"
cand = root / "cta_max_true_batch_dev_20261028/batch2_candidate"
backend = dev / "real_max_batch2_backend.py"

assert backend.is_file(), "STOP: Development backend missing"
assert cand.is_dir(), "STOP: Existing batch candidate missing"

print("=== CURRENT BACKEND GRAPH SELECTION ===")

lines = backend.read_text().splitlines()
for i, line in enumerate(lines, 1):
    if any(x in line for x in (
        "grecbase_fusion",
        "build_grecbase",
        "graph =",
        "session.load",
        "model.execute",
    )):
        print(f"{i}: {line.strip()}")

print("\n=== EXISTING BATCH-2 GRAPH BUILDERS ===")

found = 0
for base in (cand, dev):
    for p in sorted(base.rglob("*grecbase*.py")):
        if "backup" in p.name.lower():
            continue
        try:
            tree = ast.parse(p.read_text())
        except (OSError, SyntaxError, UnicodeError):
            continue

        builders = [
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and "build_grecbase" in n.name
        ]

        if builders:
            found += 1
            print("FILE:", p)
            print("BUILDERS:", ", ".join(builders))

print("\nGRAPH CANDIDATES FOUND:", found)
print("NO FILES MODIFIED")
print("NO MAX STARTUP")
PY
