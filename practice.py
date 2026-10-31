python3 -B - <<'PY'
from pathlib import Path
import shutil, hashlib

src = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
dst = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/batch2/cta_max")

folders = [
    "context_head_weights",
    "get_path_weights",
    "grecbase_aux_weights",
    "grecbase_integration_weights",
    "main_context_weights",
    "nlp_weights",
    "sequence_weights",
    "sibling_context_weights",
]

def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

if not dst.is_dir():
    raise SystemExit("STOP: clean CTA_MAX module folder missing")

for name in folders:
    if not (src / name).is_dir() or (dst / name).exists():
        raise SystemExit("STOP: missing source or existing target: " + name)

required = sum(p.stat().st_size for name in folders for p in (src / name).rglob("*") if p.is_file())
if shutil.disk_usage(dst).free < required * 2:
    raise SystemExit("STOP: insufficient disk space")

for name in folders:
    source = src / name
    target = dst / name
    shutil.copytree(source, target)
    a = {p.relative_to(source).as_posix(): sha256(p) for p in source.rglob("*") if p.is_file()}
    b = {p.relative_to(target).as_posix(): sha256(p) for p in target.rglob("*") if p.is_file()}
    if a != b:
        raise SystemExit("FAIL: weight checksum mismatch: " + name)
    print("PASS:", name, "| Files:", len(a))

print("WEIGHT FOLDERS COPIED:", len(folders))
print("ORIGINALS UNCHANGED")
PY
