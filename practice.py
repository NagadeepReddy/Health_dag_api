python3 -B - <<'PY'
from pathlib import Path
import json, hashlib

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate")
report = json.loads((root / "CTA_NATIVE_BATCH2_CPU_ACCEPTANCE_20261030.json").read_text())
records = report["staged_source_sha256"]
files = sorted(root.rglob("*.py"))

print("STAGED PYTHON FILES:", len(files))
print("REPORT CHECKSUM RECORDS:", len(records))

if isinstance(records, dict):
    print("CHECKSUM RECORD EXAMPLE:", next(iter(records.items()), None))
else:
    print("CHECKSUM RECORD EXAMPLE:", records[0] if records else None)

print("\nACTUAL SOURCE CHECKSUMS:")
for p in files:
    print(p.relative_to(root), hashlib.sha256(p.read_bytes()).hexdigest())

print("\nREAD-ONLY CHECK COMPLETE")
PY
