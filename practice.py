cd /application1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path
import tarfile, hashlib

pkg = Path("/application1/CTA_MAX_VALIDATED_RELEASE_20261028.tar.gz")
src = Path("/application1/cta_max_native_release_candidate_20261028/cta_router.py")

assert pkg.is_file() and src.is_file(), "STOP: Missing package or source"

with tarfile.open(pkg, "r:gz") as archive:
    matches = [
        m for m in archive.getmembers()
        if m.isfile() and m.name.endswith("/cta_router.py")
    ]
    assert len(matches) == 1, f"STOP: Expected one packaged router, found {len(matches)}"
    packaged = archive.extractfile(matches[0]).read()

current = src.read_bytes()
hash_of = lambda b: hashlib.sha256(b).hexdigest()

print("PACKAGED ROUTER SHA256:", hash_of(packaged))
print("CURRENT ROUTER SHA256: ", hash_of(current))

if packaged == current:
    print("RELEASE ROUTER: IDENTICAL — PASS")
else:
    print("RELEASE ROUTER: CHANGED — PACKAGE NEEDS REVALIDATION")
    import difflib
    diff = difflib.unified_diff(
        packaged.decode("utf-8").splitlines(),
        current.decode("utf-8").splitlines(),
        fromfile="packaged", tofile="current", lineterm=""
    )
    for i, line in enumerate(diff):
        if i >= 100:
            print("DIFF TRUNCATED")
            break
        print(line)

print("FILES MODIFIED: NONE")
print("MAX STARTED: NO")
PY
