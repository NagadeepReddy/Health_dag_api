python3 - <<'PY'
from pathlib import Path
import tarfile, posixpath, copy, hashlib, os

src = Path("/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102.tar.gz")
dst = Path("/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102_PORTABLE.tar.gz")
tmp = Path(str(dst) + ".partial")
root = "/application1/sajjna8/rt-pzai-bplan-v1/"

assert src.is_file(), "Original archive missing"
fixes = {}

try:
    with tarfile.open(src, "r:gz") as reader:
        members = reader.getmembers()
        names = {posixpath.normpath(m.name) for m in members}

        for m in members:
            if not m.issym():
                continue

            link = m.linkname
            if link.startswith("/"):
                assert link.startswith(root), f"External link: {link}"
                link = posixpath.relpath(
                    link[len(root):],
                    posixpath.dirname(m.name)
                )
                fixes[m.name] = link

            resolved = posixpath.normpath(
                posixpath.join(posixpath.dirname(m.name), link)
            )
            assert not resolved.startswith("../")
            assert resolved in names or any(
                n.startswith(resolved + "/") for n in names
            ), f"Missing symlink target: {m.name}"

        assert len(fixes) == 1, f"Expected one fix, found {len(fixes)}"

        print("REPAIRING:", fixes, flush=True)

        with tarfile.open(tmp, "w:gz", compresslevel=3) as writer:
            for m in members:
                item = copy.copy(m)
                if item.name in fixes:
                    item.linkname = fixes[item.name]
                writer.addfile(
                    item,
                    reader.extractfile(m) if m.isfile() else None
                )

    with tarfile.open(tmp, "r:gz") as check:
        assert len(check.getmembers()) == len(members)
        assert all(not m.linkname.startswith("/")
                   for m in check if m.issym())

    os.replace(tmp, dst)

    h = hashlib.sha256()
    with dst.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)

    Path(str(dst) + ".sha256").write_text(
        f"{h.hexdigest()}  {dst.name}\n"
    )

    print("BPLAN PORTABLE ARCHIVE: PASS")
    print("ORIGINAL ARCHIVE: UNCHANGED")
    print("NEW ARCHIVE:", dst)
    print("SIZE MB:", round(dst.stat().st_size / 1048576))

finally:
    tmp.unlink(missing_ok=True)
PY
