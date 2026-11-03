python3 - <<'PY'
import tarfile, hashlib
from pathlib import Path

base = Path("/application1")
old = base / "BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_FINAL.tar.gz"
new = base / "BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_CLEAN.tar.gz"

def contents(path):
    result = {}
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            if member.isfile():
                h = hashlib.sha256()
                source = archive.extractfile(member)
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    h.update(block)
                result[member.name] = ("file", h.hexdigest())
            elif member.issym() or member.islnk():
                result[member.name] = ("link", member.linkname)
    return result

original = contents(old)
clean = contents(new)
removed = set(original) - set(clean)
added = set(clean) - set(original)
changed = [p for p in clean.keys() & original.keys()
           if clean[p] != original[p]]

allowed = (".pre_bridge_backup", ".pre_typed_queue_backup",
           ".before_response_trace")

assert len(removed) == 4, f"Unexpected removals: {removed}"
assert all(p.endswith(allowed) for p in removed), removed
assert not added, f"Unexpected additions: {added}"
assert not changed, f"Changed files: {changed}"

print("BPLAN EXECUTABLE FILE PARITY: PASS")
print("REMOVED OLD BACKUPS:", len(removed))
print("CHANGED WORKING FILES:", len(changed))
print("BPLAN CLEAN HANDOFF CONTENT: PASS")
print("ORIGINAL VALIDATED RELEASE: PRESERVED")
PY
