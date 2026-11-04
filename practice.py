cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
from datetime import datetime
import re

base = Path("artifacts/v1.472-max/pzaas_max")
validation = base / "validation"

targets = [
    "ppa_model_base_reference.pt",
    "pzaas_eight_branch_targets.npz",
    "ppa_pytorch_reference_01.pt",
    "ppa_model_input_exact.pt",
]

print("=== PZAAS REFERENCE PROVENANCE CHECK ===")

for name in targets:
    p = validation / name
    if p.is_file():
        s = p.stat()
        print(
            f"FOUND: {name} | "
            f"size={s.st_size} | "
            f"modified={datetime.fromtimestamp(s.st_mtime)}"
        )
    else:
        print("MISSING:", name)

print("\n=== ARTIFACT GENERATION SOURCE ===")

extensions = {".py", ".sh", ".md", ".json"}
matches = {name: [] for name in targets}

for p in base.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in extensions:
        continue
    if p.stat().st_size > 2_000_000:
        continue

    try:
        lines = p.read_text(errors="replace").splitlines()
    except OSError:
        continue

    for i, line in enumerate(lines):
        for name in targets:
            if name in line:
                lo = max(0, i - 3)
                hi = min(len(lines), i + 5)
                matches[name].append((p, i + 1, lines[lo:hi], lo))

for name in targets:
    print(f"\nARTIFACT: {name}")
    hits = matches[name][:8]
    if not hits:
        print("GENERATION SOURCE: NOT FOUND IN SAVED FILES")
        continue

    for path, lineno, snippet, start in hits:
        print(f"FILE: {path}:{lineno}")
        for j, line in enumerate(snippet, start + 1):
            print(f"  {j}: {line[:220]}")

print("\n=== NEXT DECISION ===")
if matches[targets[0]] and matches[targets[1]]:
    print("BOTH GENERATION SOURCES LOCATED")
    print("NEXT: VERIFY IDENTICAL MODEL INPUT AND OUTPUT STAGE")
else:
    print("SAME-INPUT PROVENANCE: NOT YET ESTABLISHED")
    print("DO NOT PATCH MAX BASED ON UNVERIFIED REFERENCE")

print("FILES MODIFIED: NONE")
print("ORIGINAL DS: UNCHANGED")
PY
