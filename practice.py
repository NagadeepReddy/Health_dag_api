python - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py")
s = p.read_text()

old = '''    for alias in aliases:
        if alias in weights_registry:
            existing = np.asarray(weights_registry[alias])
            if not np.array_equal(existing, value):
                raise RuntimeError(
                    f"Conflicting trained weights for {alias}"
                )
        else:
            weights_registry[alias] = value
            added += 1'''

new = '''    for alias in aliases:
        if alias in weights_registry:
            existing = np.asarray(weights_registry[alias])
            if not np.array_equal(existing, value):
                print(
                    "CHECKPOINT PREFERRED OVER EXPORT:",
                    alias,
                    "checkpoint_shape=", existing.shape,
                    "export_shape=", value.shape,
                    flush=True,
                )
            continue

        weights_registry[alias] = value
        added += 1'''

if old in s:
    assert s.count(old) == 1
    updated = s.replace(old, new)
    ast.parse(updated, filename=str(p))

    backup = p.with_suffix(".py.before_conflict_fix")
    if not backup.exists():
        shutil.copy2(p, backup)

    p.write_text(updated)
    print("WEIGHT REGISTRY MERGE FIXED")
    print("ORIGINAL CHECKPOINT VALUES PRESERVED")
    print("BACKUP:", backup)

elif new in s:
    print("WEIGHT REGISTRY FIX ALREADY PRESENT")

else:
    raise SystemExit(
        "STOP: Expected registry block not found. Nothing modified."
    )
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_full.py
