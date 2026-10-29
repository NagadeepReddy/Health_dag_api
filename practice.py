cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import json
import hashlib

roots = [
    Path("artifacts/v1.168-max"),
    Path("artifacts/v1.168"),
    Path("/application1/cta_max_true_batch_dev_20261028"),
    Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"),
]

seen = {}
checked = 0

for root in roots:
    if not root.exists():
        continue

    for p in root.rglob("*.json"):
        if not p.is_file() or p.stat().st_size > 10_000_000:
            continue
        checked += 1

        try:
            data = json.loads(p.read_text())
        except (OSError, ValueError, UnicodeError):
            continue

        if not isinstance(data, dict):
            continue

        # Existing real CTA request contract.
        required = {"ClientFeature", "Events", "profile"}
        if not required.issubset(data):
            continue

        fingerprint = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

        seen.setdefault(fingerprint, []).append(str(p.resolve()))

print("=== DISTINCT GENUINE CTA REQUEST CANDIDATES ===")
for i, (fingerprint, paths) in enumerate(seen.items(), 1):
    print(f"INPUT {i} | SHA256: {fingerprint[:16]}")
    print("FILE:", paths[0])
    print("DUPLICATE COPIES:", len(paths) - 1)

print("\nJSON FILES CHECKED:", checked)
print("UNIQUE CTA REQUESTS:", len(seen))
print("DISTINCT INPUTS READY:", "YES" if len(seen) >= 2 else "NO")
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
