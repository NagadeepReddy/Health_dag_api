cd /application1 || exit 1

python3 -S -B - <<'PY'
from pathlib import Path
import ast, copy, hashlib, io, os, tarfile

root = Path("/application1")
old = root / "CTA_MAX_VALIDATED_RELEASE_20261028.tar.gz"
src = root / "cta_max_native_release_candidate_20261028/cta_router.py"
new = root / "CTA_MAX_UPDATED_RELEASE_20261028.tar.gz"
sha = Path(str(new) + ".sha256")
tmp = Path(str(new) + ".part")

assert old.is_file() and src.is_file(), "STOP: Missing original package or router"
assert not new.exists() and not sha.exists() and not tmp.exists(), "STOP: Output already exists"

router = src.read_bytes()
ast.parse(router.decode("utf-8"))
print("UPDATED ROUTER SYNTAX: PASS")

with tarfile.open(old, "r:gz") as original:
    members = original.getmembers()
    matches = [
        m for m in members
        if m.isfile() and m.name.endswith("/cta_router.py")
    ]
    assert len(matches) == 1, "STOP: Packaged router not uniquely identified"

    with tarfile.open(tmp, "w:gz") as output:
        for member in members:
            if member is matches[0]:
                updated = copy.copy(member)
                updated.size = len(router)
                updated.mtime = int(src.stat().st_mtime)
                output.addfile(updated, io.BytesIO(router))
            elif member.isfile():
                output.addfile(member, original.extractfile(member))
            else:
                output.addfile(member)

with tarfile.open(tmp, "r:gz") as check:
    assert check.getnames() == [m.name for m in members]
    assert check.extractfile(matches[0].name).read() == router
    assert check.getmembers()[-1] is not None

os.replace(tmp, new)

digest = hashlib.sha256(new.read_bytes()).hexdigest()
sha.write_text(f"{digest}  {new.name}\n")

print("UPDATED RELEASE PACKAGE: CREATED")
print("ROUTER CONTENT: VERIFIED")
print("SHA256:", digest)
print("ORIGINAL VALIDATED PACKAGE: PRESERVED")
print("DS CODE: UNCHANGED")
print("MAX STARTED: NO")
print("LIVE VALIDATION: STILL REQUIRED")
PY
