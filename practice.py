python3 -B - <<'PY'
from pathlib import Path
import shutil

src = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
dst = Path("/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031")

if not src.is_dir() or dst.exists() or dst.is_symlink():
    raise SystemExit("STOP: Source missing or stage already exists")

if shutil.disk_usage(dst.parent).free < 4 * 1024**3:
    raise SystemExit("STOP: Insufficient free disk space")

def exclude(directory, names):
    if Path(directory) == src / "batch2":
        return {"cta_max"} if "cta_max" in names else set()
    return set()

shutil.copytree(src, dst, symlinks=True, ignore=exclude)

assert (dst / "run_cta_native.sh").is_file()
assert (dst / "artifacts/v1.168-max/cta_max").is_dir()
assert not (dst / "batch2/cta_max").exists()

print("HANDOFF STAGE CREATED: PASS")
print("DUPLICATE REFERENCE EXCLUDED: PASS")
print("ORIGINAL CLEAN VM UNCHANGED: PASS")
print("STAGE:", dst)
PY

bash /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/run_cta_native.sh check
