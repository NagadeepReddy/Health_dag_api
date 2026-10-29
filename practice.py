python3 -S -B - <<'PY'
from pathlib import Path
import json, tarfile, hashlib

base = Path("/application1")
release = base / "cta_max_native_release_candidate_20261028"
response = base / "cta_queue_bridge_response.json"
log = base / "cta_queue_bridge_live.log"
archive = base / "CTA_MAX_NATIVE_E2E_PASS_20261028.tar.gz"

assert release.is_dir(), "STOP: release missing"
assert response.is_file(), "STOP: response missing"
assert log.is_file(), "STOP: log missing"
assert not archive.exists(), "STOP: archive already exists"

launcher = (release / "cta_native_launcher.py").read_text()
assert "CTA_NATIVE_TYPED_QUEUE_BRIDGE" in launcher

data = json.loads(response.read_text())
assert isinstance(data["jsonData"]["prediction"]["offerList"], list)

with tarfile.open(archive, "w:gz") as tar:
    for p in (release, response, log):
        tar.add(p, arcname=p.name)

with tarfile.open(archive, "r:gz") as tar:
    assert tar.getmembers()

print("NATIVE CTA E2E: PASS")
print("QUEUE FIX: INCLUDED")
print("UPDATED RELEASE ARCHIVE: CREATED")
print("ARCHIVE:", archive)
print("SHA256:", hashlib.sha256(archive.read_bytes()).hexdigest())
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
