python3 -B - <<'PY'
from pathlib import Path
from collections import defaultdict
import hashlib, json

base = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max")
release = base / "cta_native_batch2_release_candidate"

roots = [
    base,
    Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"),
    Path("/application1/cta_max_true_batch_dev_20261028")
]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

staged = sorted(release.rglob("*.py"))
others = defaultdict(list)

for root in roots:
    if not root.is_dir():
        continue
    for p in root.rglob("*.py"):
        if release in p.parents or "__pycache__" in p.parts:
            continue
        others[p.name].append(p)

print("=== STAGED CODE COMPARISON ===")
print("Staged Python files:", len(staged))

for p in staged:
    matches = others[p.name]
    staged_hash = digest(p)
    identical = sum(digest(q) == staged_hash for q in matches)
    different = len(matches) - identical
    print(f"{p.name}: identical={identical}, different={different}")

report = release / "CTA_NATIVE_BATCH2_CPU_ACCEPTANCE_20261030.json"
print("\n=== ACCEPTANCE REPORT ===")
if report.is_file():
    data = json.loads(report.read_text())
    print("Report: FOUND")
    print("Top-level fields:", ", ".join(data.keys()))
else:
    print("Report: MISSING")

print("\nREAD-ONLY AUDIT COMPLETE")
PY
