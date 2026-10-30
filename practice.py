python3 -B - <<'PY'
from pathlib import Path

base = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/"
    "cta_native_batch2_release_candidate/"
    "cta_batch2_worker_bootstrap"
)

active = base / "sitecustomize.py"
disabled = base / "sitecustomize.py.disabled"

if active.is_symlink() or disabled.is_symlink():
    raise SystemExit("STOP: Unexpected symlink")

if active.exists():
    if disabled.exists():
        raise SystemExit("STOP: Disabled backup already exists")
    active.rename(disabled)
    print("EXPERIMENTAL STARTUP HOOK: DISABLED")
else:
    print("STARTUP HOOK: ALREADY ABSENT")

print("WORKING NATIVE RELEASE: UNCHANGED")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("MODEL EXECUTIONS: ZERO")
PY
