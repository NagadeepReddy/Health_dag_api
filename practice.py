python3 -B - <<'PY'
from pathlib import Path
import shutil
import filecmp

root = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030")
src = root / "batch2/cta_max"
dst = root / "artifacts/v1.168-max/cta_max"

required = src / "grecbase_aux_weights/task_embedding.0.weight.npy"

if not required.is_file() or not dst.is_dir():
    raise SystemExit("STOP: Reference weight or destination missing")

missing = []

for folder in sorted(src.iterdir()):
    if not folder.name.endswith("_weights") or not folder.is_dir():
        continue
    if folder.is_symlink():
        raise SystemExit(f"STOP: Source symlink: {folder}")
    target_dir = dst / folder.name
    if target_dir.is_symlink():
        raise SystemExit(f"STOP: Destination symlink: {target_dir}")
    for f in folder.rglob("*"):
        if f.is_symlink():
            raise SystemExit(f"STOP: Weight symlink: {f}")
        if f.is_file():
            target = target_dir / f.relative_to(folder)
            if not target.exists():
                missing.append((f, target))

needed = sum(f.stat().st_size for f, _ in missing)
free = shutil.disk_usage(dst).free

print("MISSING FILES:", len(missing))
print("REQUIRED SPACE MB:", round(needed / 1048576, 1))

if free < needed + 100 * 1048576:
    raise SystemExit("STOP: Insufficient disk space")

for f, target in missing:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, target)
    if not filecmp.cmp(f, target, shallow=False):
        raise SystemExit(f"STOP: Copy mismatch: {target}")
    print("RESTORED:", target.relative_to(dst))

assert (dst / "grecbase_aux_weights/task_embedding.0.weight.npy").is_file()
print("CLEAN REMAINING WEIGHT PACKAGING: PASS")
PY
