python3 - <<'PY'
import tarfile
import re
from pathlib import Path

archive = Path("/application1/BPLAN_MAX_SINGLE_REQUEST_HANDOFF_20261102.tar.gz")
required = [
    "artifacts/v1.113/core-artifact/pipeline.py",
    "artifacts/v1.113/core-artifact/base_model.pt",
    "artifacts/v1.113/core-artifact/bplan_model.pt",
    "artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_launcher.py",
    "artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev/bplan_native_scheduler.py",
]

with tarfile.open(archive, "r:gz") as tar:
    members = {m.name.lstrip("./"): m for m in tar.getmembers()}
    missing = [p for p in required if p not in members]
    weights = [p for p in members if "max_weights/" in p and members[p].isfile()]
    symlinks = [(p, m.linkname) for p, m in members.items() if m.issym()]
    external = []
    for name, member in members.items():
        if not member.isfile() or not name.endswith(".py"):
            continue
        f = tar.extractfile(member)
        if not f:
            continue
        for i, line in enumerate(f.read().decode("utf-8", "replace").splitlines(), 1):
            if re.search(r"/application1/|/home/|/var/|CTA_MAX_TEAM_HANDOFF", line):
                external.append(f"{name}:{i}: {line.strip()[:120]}")

    print("REQUIRED FILES:", "PASS" if not missing else "MISSING")
    for p in missing: print("MISSING:", p)
    print("MAX WEIGHT FILES:", len(weights))
    print("SYMLINKS:", symlinks[:10])
    print("ABSOLUTE PATH REFERENCES:", len(external))
    for x in external[:15]: print(x)
    print("PORTABILITY REVIEW:", "PASS" if not missing and not symlinks and not external and weights else "NEEDS REVIEW")
PY
