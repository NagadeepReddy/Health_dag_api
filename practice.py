ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

ROOT="$ROOT" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["ROOT"])
dev = root / "bplan_max_dev"
stage = root / "bplan_helper_weights_stage"

assert dev.is_dir() and stage.is_dir(), "STOP: BPLAN directories missing"
assert (stage / "mapping.json").is_file(), "STOP: validated mapping missing"

old = "artifacts/v1.168-max/cta_max"
new = str(stage)
changes = []

# Link helper directories without copying or modifying trained weights.
for source in sorted(stage.iterdir()):
    if not source.is_dir():
        continue
    target = dev / source.name
    if target.is_symlink():
        assert target.resolve() == source.resolve(), f"STOP: wrong link {target}"
    elif target.exists():
        raise RuntimeError(f"STOP: existing helper directory needs review: {target}")
    else:
        target.symlink_to(source.resolve(), target_is_directory=True)
        print("LINKED:", target.name)

# Replace only the known CTA artifact prefix in isolated MAX files.
for file in sorted(dev.glob("*.py")):
    content = file.read_text()
    if old not in content:
        continue
    updated = content.replace(old, new)
    changes.append((file, content, updated))

for file, original, updated in changes:
    backup = file.with_suffix(".py.before_bplan_weights")
    assert not backup.exists(), f"STOP: backup already exists: {backup}"

for file, original, updated in changes:
    backup = file.with_suffix(".py.before_bplan_weights")
    backup.write_text(original)
    file.write_text(updated)
    print("UPDATED:", file.name)

print("BPLAN WEIGHT PATH CONNECTION: PASS")
print("FILES UPDATED:", len(changes))
print("ORIGINAL DS AND CTA: UNCHANGED")
print("NEXT: ADAPT BPLAN-SPECIFIC GRAPH DIMENSIONS")
PY
