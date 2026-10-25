cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()
needle = 'print("CTA_NATIVE_FACTORY_ENTERED", flush=True)'

if needle not in s:
    raise SystemExit("Factory marker not found; no changes made")

if "faulthandler.dump_traceback_later" not in s:
    updated = s.replace(
        needle,
        needle + "\n        import faulthandler\n        faulthandler.dump_traceback_later(25, repeat=False)",
        1
    )
    p.with_suffix(".py.worker_trace_backup").write_text(s)
    p.write_text(updated)

py_compile.compile(str(p), doraise=True)
print("CTA WORKER STACK TRACE: INSTALLED")
print("ORIGINAL DS CODE: UNCHANGED")
PY

P="podman --root /application1/podman/storage --runroot /run/containers/storage"
STAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
$P start cta-native-live
sleep 35
$P logs --since "$STAMP" --tail 110 cta-native-live 2>&1
