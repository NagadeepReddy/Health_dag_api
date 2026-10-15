python3 - <<'PY'
from pathlib import Path

repo = Path.cwd()
release = Path("../cta-max-release-review").resolve()
source = repo / "artifacts/v1.168-max/cta_max"
target = release / "artifacts/v1.168-max/cta_max"

def link(src, dst):
    if dst.exists() or dst.is_symlink():
        print("ALREADY EXISTS:", dst.name)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to(src.resolve(), target_is_directory=src.is_dir())
    print("LINKED:", dst.name)

# Original DS model and configuration — read-only reference
link(repo / "artifacts/v1.168",
     release / "artifacts/v1.168")

# MAX exported weight directories
for folder in sorted(source.iterdir()):
    if folder.is_dir() and any(
        p.suffix in (".npy", ".npz", ".pt")
        for p in folder.rglob("*") if p.is_file()
    ):
        link(folder, target / folder.name)

print("RELEASE ASSET REFERENCES: READY")
print("ORIGINAL DS CODE: UNCHANGED")
print("NO MODEL WEIGHTS COPIED OR DELETED")
PY
