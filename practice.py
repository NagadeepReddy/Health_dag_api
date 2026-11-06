
cd /application1/sajjna8 && python3 - <<'PY'
from pathlib import Path
import ast
import difflib
import re

base = Path("/application1/sajjna8")

sources = {
    "BPLAN": base / (
        "rt-pzai-bplan-v1/artifacts/v1.113-max/"
        "maxserve_bplan_extension"
    ),
    "PZAAS": base / (
        "PZAAS_MAX_CLEAN_HANDOFF_20261106/model/"
        "artifacts/v1.472-max/maxserve_pzaas_extension"
    )
}

def locate(root, filename):
    matches = [
        p for p in root.rglob(filename)
        if "reference" not in str(p).lower()
        and "backup" not in str(p).lower()
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"STOP: Expected one {filename}, found {len(matches)}"
        )
    return matches[0]

print("=== SHARED QUEUE COMPATIBILITY REVIEW ===")

files = {}
for name, root in sources.items():
    path = locate(root, f"{name.lower()}_queue_compat.py")
    source = path.read_text()
    ast.parse(source)
    files[name] = source
    print(f"{name}: {path}")
    print(f"LINES: {len(source.splitlines())}")

def normalize(text):
    return re.sub(
        "bplan|pzaas", "model", text,
        flags=re.IGNORECASE
    )

bplan = normalize(files["BPLAN"])
pzaas = normalize(files["PZAAS"])

print("\n=== IMPLEMENTATION COMPARISON ===")
print("NORMALIZED SOURCE IDENTICAL:", bplan == pzaas)

diff = list(difflib.unified_diff(
    bplan.splitlines(),
    pzaas.splitlines(),
    fromfile="BPLAN",
    tofile="PZAAS",
    lineterm=""
))

if diff:
    print("DIFFERENCES:")
    print("\n".join(diff[:100]))
else:
    print("NO DIFFERENCES AFTER MODEL-NAME NORMALIZATION")

print("\n=== QUEUE IMPLEMENTATION ===")
for n, line in enumerate(
    files["PZAAS"].splitlines(), 1
):
    print(f"{n:3}: {line}")

print("\n=== BPLAN WORKER ADAPTER LOCATION ===")
root = sources["BPLAN"]

for path in sorted(root.rglob("*worker*adapter*.py")):
    if "reference" not in str(path).lower():
        print(path.relative_to(root))

print("\n=== RESULT ===")
print("SHARED QUEUE REVIEW: COMPLETE")
print("EXISTING MODELS: UNCHANGED")
print("RUNNING CONTAINERS: UNCHANGED")
print("NEXT: BUILD SHARED QUEUE MODULE")
PY
