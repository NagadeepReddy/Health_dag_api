python3 -S -B - <<'PY'
from pathlib import Path
import json, tarfile, hashlib, io

base = Path("/application1")
repo = base / "sajjna8/rt-pzaas-cta-offers-v1"
tests = repo / "artifacts/v1.168-max/test-results"
release = base / "cta_max_native_release_candidate_20261028"

input_file = tests / "cta_max_tiles_smoketest_input.json"
baseline = tests / "cta_max_tiles_response.json"
log = base / "cta_dual_queue_retest_20261029.log"
responses = [
    base / "cta_dual_queue_response_1.json",
    base / "cta_dual_queue_response_2.json",
]

required = [input_file, baseline, log, *responses]
assert release.is_dir(), "STOP: Release directory missing"
assert all(p.is_file() for p in required), "STOP: Evidence missing"

expected = json.loads(baseline.read_text())
expected = expected.get("jsonData", expected)["prediction"]

for i, p in enumerate(responses, 1):
    result = json.loads(p.read_text())
    actual = result.get("jsonData", result)["prediction"]
    assert actual == expected, f"STOP: Request {i} parity failed"
    print(f"REQUEST {i}: EXACT BUSINESS PARITY PASS")

events = log.read_text(errors="replace")
assert events.count("CTA HTTP RESPONSE DELIVERED:") == 2, \
    "STOP: Two deliveries not confirmed"

archive = base / "CTA_MAX_NATIVE_CONCURRENT2_PASS_20261029.tar.gz"
assert not archive.exists(), "STOP: Archive already exists"

manifest = {
    "milestone": "Native built-in MAX Serve concurrent-2 PASS",
    "requests": 2,
    "http_statuses": [200, 200],
    "business_parity": [True, True],
    "latency_seconds": [113.72, 111.92],
    "throughput_rps": 0.0176,
    "ds_code_changed_by_test": False,
    "native_batching_verified": False,
    "gpu_verified": False,
    "image_approved": False,
}

with tarfile.open(archive, "w:gz") as tar:
    tar.add(release, arcname="release_candidate")
    for p in required:
        tar.add(p, arcname="evidence/" + p.name)

    content = json.dumps(manifest, indent=2).encode()
    info = tarfile.TarInfo("evidence/milestone.json")
    info.size = len(content)
    tar.addfile(info, io.BytesIO(content))

print("NATIVE CONCURRENT-2: PASS")
print("WORKING RELEASE AND EVIDENCE: ARCHIVED")
print("ARCHIVE:", archive)
print("SHA256:", hashlib.sha256(archive.read_bytes()).hexdigest())
print("MAX STARTUP: NOT PERFORMED")
print("DS CODE: UNCHANGED")
PY
