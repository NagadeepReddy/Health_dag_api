python3 -B - <<'PY'
from pathlib import Path
import hashlib, json, shutil

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
src = repo / "artifacts/v1.168-max/cta_native_batch2_release_candidate"
dst = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
report_file = src / "CTA_NATIVE_BATCH2_CPU_ACCEPTANCE_20261030.json"

report = json.loads(report_file.read_text())
expected = report["staged_source_sha256"]
actual = {
    p.relative_to(src).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in src.rglob("*.py")
}

if expected != actual or len(actual) != 20:
    raise SystemExit("STOP: validated source checksums do not match")

if dst.exists():
    raise SystemExit("STOP: clean folder already exists; no overwrite")

target = dst / "artifacts/v1.168-max/cta_native_batch2_release_candidate"

for relative in sorted(expected):
    source = src / relative
    output = target / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output)

shutil.copy2(report_file, target / report_file.name)

for relative, checksum in expected.items():
    copied = target / relative
    if hashlib.sha256(copied.read_bytes()).hexdigest() != checksum:
        raise SystemExit("STOP: copied checksum mismatch: " + relative)

print("CLEAN VM FOLDER:", dst)
print("VERIFIED PYTHON FILES COPIED:", len(expected))
print("ACCEPTANCE REPORT: COPIED")
print("COPIED CHECKSUMS: PASS")
print("ORIGINAL FILES: UNCHANGED")
PY
