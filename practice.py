python3 -B - <<'PY'
from pathlib import Path
import json, hashlib

root = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate")
report = json.loads((root / "CTA_NATIVE_BATCH2_CPU_ACCEPTANCE_20261030.json").read_text())
expected = report["staged_source_sha256"]
actual = {
    p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in root.rglob("*.py")
}

for name in sorted(set(expected) | set(actual)):
    status = "PASS" if name in expected and name in actual and expected[name] == actual[name] else "FAIL"
    print(status, name)

print("REPORT FILES:", len(expected))
print("ACTUAL FILES:", len(actual))
print("ALL CHECKSUMS MATCH:", expected == actual)
PY
