python3 - <<'PY'
from pathlib import Path
import tarfile, zipfile, hashlib, shutil

stage = Path("/application1/BPLAN_MAX_FRESH_HANDOFF_TEST_20261102")
dest = stage / "artifacts/v1.113/lookup/page_seq_2.csv"
suffix = "v1.113/lookup/page_seq_2.csv"

matches = []
checked = 0

for base in (Path("/application1"), Path("/vzhome")):
    if not base.exists():
        continue

    for p in base.rglob("*"):
        if "/podman/" in str(p) or not p.is_file():
            continue

        name = p.name.lower()
        if not name.endswith((".tar.gz", ".tgz", ".tar", ".zip")):
            continue

        # Already-created handoff packages are known to lack this file.
        if name.startswith("bplan_max_single_request_handoff_"):
            continue

        checked += 1
        try:
            if zipfile.is_zipfile(p):
                with zipfile.ZipFile(p) as z:
                    for n in z.namelist():
                        if n.endswith(suffix):
                            matches.append((p, n, "zip"))
            elif tarfile.is_tarfile(p):
                with tarfile.open(p, "r:*") as t:
                    for m in t:
                        if m.isfile() and m.name.endswith(suffix):
                            matches.append((p, m.name, "tar"))
        except (OSError, tarfile.TarError, zipfile.BadZipFile) as e:
            print("SKIPPED:", p, str(e)[:100])

print("ARCHIVES CHECKED:", checked)
print("EXACT V1.113 MATCHES:", len(matches))

contents = {}

for path, member, kind in matches:
    if kind == "zip":
        with zipfile.ZipFile(path) as z:
            data = z.read(member)
    else:
        with tarfile.open(path, "r:*") as t:
            data = t.extractfile(member).read()

    if data:
        digest = hashlib.sha256(data).hexdigest()
        contents[digest] = data
        print("FOUND:", path, member, "SHA256:", digest)

if len(contents) == 1:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        assert hashlib.sha256(dest.read_bytes()).hexdigest() in contents, \
            "STOP: Existing lookup differs"
    else:
        dest.write_bytes(next(iter(contents.values())))
    print("BPLAN ORIGINAL LOOKUP RECOVERED: PASS")
    print("DESTINATION:", dest)
elif len(contents) > 1:
    print("STOP: Conflicting versions. No file written.")
else:
    print("BPLAN LOOKUP NOT FOUND IN LOCAL ARCHIVES")
    print("Original v1.113 model artifact storage is needed.")
PY
