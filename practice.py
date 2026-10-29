python3 -S -B - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
assert root.is_dir(), "STOP: Artifacts directory missing"

print("=== EXISTING BASELINE FILES ===")

found = []
for p in root.rglob("*.json"):
    name = p.name.lower()
    if any(k in name for k in (
        "fills", "response", "pytorch", "baseline", "result"
    )):
        found.append(p)

for p in sorted(found):
    print(p, "|", p.stat().st_size, "bytes")

print("TOTAL:", len(found))
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
