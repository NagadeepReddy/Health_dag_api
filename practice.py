python3 - <<'PY'
from pathlib import Path
import re, ast

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
dev = root / "bplan_max_dev"
assert (root / "max_weights/manifest.json").is_file()

pattern = re.compile(
    r"""(?m)^WDIR\s*=\s*Path\(__file__\)\.parent\s*/\s*['"]grecbase_integration_weights['"]\s*$"""
)
replacement = 'WDIR = Path(__file__).resolve().parent.parent / "max_weights"'

changes = []
for p in sorted(dev.glob("*.py")):
    original = p.read_text()
    updated, count = pattern.subn(replacement, original)
    if count:
        ast.parse(updated, filename=str(p))
        changes.append((p, updated, count))

assert changes, "STOP: No helper weight paths matched"

for p, updated, count in changes:
    p.write_text(updated)
    print(f"UPDATED: {p.name} ({count})")

print("BPLAN MAX HELPER WEIGHT PATHS: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
