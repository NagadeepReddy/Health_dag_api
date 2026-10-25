cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()
old = "faulthandler.dump_traceback_later(25, repeat=False)"
new = "faulthandler.dump_traceback_later(3, repeat=False)"

if old not in s:
    raise SystemExit("Expected trace timer not found. No changes made.")

p.write_text(s.replace(old, new, 1))
py_compile.compile(str(p), doraise=True)
print("CTA EARLY WORKER TRACE: READY")
PY

P="podman --root /application1/podman/storage --runroot /run/containers/storage"
STAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

$P start cta-native-live
sleep 15
$P logs --since "$STAMP" --tail 180 cta-native-live 2>&1
