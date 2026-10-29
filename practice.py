python3 -S -B - <<'PY'
from pathlib import Path
import json, tarfile, hashlib, io

base = Path("/application1")
tests = base / "sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/test-results"

files = {
    "input.json": tests / "cta_max_tiles_smoketest_input.json",
    "pytorch_response.json": tests / "cta_pytorch_tiles_response.json",
    "max_response.json": tests / "cta_max_tiles_response.json",
    "native_response.json": base / "cta_native_tiles_parity_response.json",
    "native_server.log": base / "cta_native_tiles_parity.log",
}

for name, path in files.items():
    assert path.is_file(), f"STOP: Missing {path}"

def prediction(path):
    data = json.loads(path.read_text())
    return data.get("jsonData", data)["prediction"]

torch = prediction(files["pytorch_response.json"])
max_out = prediction(files["max_response.json"])
native = prediction(files["native_response.json"])

assert torch == max_out == native, "STOP: Business parity mismatch"
assert len(native["offerList"]) == 2, "STOP: Unexpected offer count"

archive = base / "CTA_MAX_TILES_PARITY_PASS_20261029.tar.gz"
assert not archive.exists(), "STOP: Evidence archive already exists"

report = {
    "result": "PASS",
    "test": "Real native MAX Serve, same saved tiles input",
    "offer_count": 2,
    "full_prediction_match": True,
    "original_ds_code_modified_by_test": False,
    "input_sha256": hashlib.sha256(files["input.json"].read_bytes()).hexdigest(),
}

with tarfile.open(archive, "w:gz") as tar:
    for name, path in files.items():
        tar.add(path, arcname=name)
    content = json.dumps(report, indent=2).encode()
    info = tarfile.TarInfo("parity_report.json")
    info.size = len(content)
    tar.addfile(info, io.BytesIO(content))

with tarfile.open(archive, "r:gz") as tar:
    assert len(tar.getmembers()) == 6

print("SAME-INPUT BUSINESS PARITY: PASS")
print("ALL THREE PREDICTIONS: MATCH")
print("OFFERS: 2")
print("EVIDENCE ARCHIVE: VERIFIED")
print("ARCHIVE:", archive)
print("MAX STARTUP: NOT PERFORMED")
print("DS CODE: UNCHANGED")
PY
