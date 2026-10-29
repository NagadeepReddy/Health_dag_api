cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path

repo = Path.cwd()
dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
base = repo / "artifacts/v1.168-max/cta_max"

files = sorted(
    [p for p in base.glob("grecbase_fusion*.py") if p.is_file()]
    + [p for p in dev.glob("grecbase_fusion*.py") if p.is_file()]
)

keywords = (
    "sibling",
    "sibling_vl",
    "sibling_pool",
    "outs =",
)

print("=== ORIGINAL VS BATCH-2 SIBLING FUSION ===")

for p in files:
    lines = p.read_text(errors="replace").splitlines()
    matches = [
        i for i, line in enumerate(lines)
        if any(k in line.lower() for k in keywords)
    ]

    if not matches:
        continue

    # Prioritize the original and active batch-2 graph.
    if (
        p.parent == dev
        and "batch2_auxfix" not in p.name
        and "batch2_diagnostic" not in p.name
    ):
        continue

    print("\nFILE:", p)
    selected = set()

    for i in matches[:12]:
        selected.update(range(max(0, i - 5), min(len(lines), i + 7)))

    for i in sorted(selected):
        print(f"{i+1}: {lines[i]}")

print("\n=== SIBLING-SPECIFIC MODULES ===")

for directory in (base, dev):
    for p in sorted(directory.glob("*sibling*.py")):
        print("\nFILE:", p)
        lines = p.read_text(errors="replace").splitlines()
        for i, line in enumerate(lines[:100], 1):
            print(f"{i}: {line}")

print("\nAUDIT: COMPLETE")
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
