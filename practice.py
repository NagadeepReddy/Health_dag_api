cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import os

repo = Path.cwd()
source_root = repo / "artifacts/v1.168-max/cta_max"
candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max"
)

required = (
    "main_context_weights",
    "context_head.deep_embedding.0.weight.npy"
)

assert source_root.is_dir(), "STOP: Original MAX directory missing"
assert candidate.is_dir(), "STOP: Batch candidate missing"

folders = sorted(
    p for p in source_root.iterdir()
    if p.is_dir() and p.name.endswith("_weights")
)

assert folders, "STOP: No original exported weight directories"

source = source_root / required[0]
assert (source / required[1]).is_file(), (
    "STOP: Main-context weight not found in original exports"
)

changes = []

# Validate everything before creating links.
for folder in folders:
    files = sorted(folder.glob("*.npy"))
    if not files:
        continue

    for p in files:
        with p.open("rb") as f:
            assert f.read(6) == b"\x93NUMPY", (
                f"STOP: Invalid weight: {p}"
            )

    target = candidate / folder.name
    container_source = (
        "/workspace/" + folder.relative_to(repo).as_posix()
    )

    if target.is_symlink():
        assert os.readlink(target) == container_source, (
            f"STOP: Conflicting link: {target}"
        )
        print("ALREADY LINKED:", folder.name)
    elif target.exists():
        assert target.is_dir(), (
            f"STOP: Unexpected existing file: {target}"
        )
        print("EXISTING DIRECTORY PRESERVED:", folder.name)
    else:
        changes.append((target, container_source, len(files)))

for target, container_source, count in changes:
    target.symlink_to(container_source, target_is_directory=True)
    print("LINKED:", target.name, "| WEIGHTS:", count)

print("MAIN-CONTEXT WEIGHT: FOUND")
print("NEW WEIGHT LINKS:", len(changes))
print("DS CODE: UNCHANGED")
print("WORKING MODEL: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
