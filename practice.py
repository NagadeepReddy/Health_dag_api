python3 -B - <<'PY'
import json
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate/CTA_NATIVE_BATCH2_CPU_ACCEPTANCE_20261030.json")
data = json.loads(p.read_text())

print("=== VALIDATED EXECUTION DETAILS ===")
for key, value in data.items():
    if any(word in key.lower() for word in
           ("runtime", "container", "launch", "environment", "test", "result", "scope")):
        print(f"{key}: {str(value)[:1200]}")

print("READ-ONLY CHECK COMPLETE")
PY
