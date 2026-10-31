CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030
export PODMAN_ROOT=/application1/podman/storage
export PODMAN_RUNROOT=/run/containers/storage
export CTA_IMAGE=localhost/cta-max-faiss:local

python3 -B - <<'PY'
from pathlib import Path

p = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/run_cta_native.sh")
s = p.read_text()

old = "  --tmpfs /tmp:rw,size=2g,mode=1777 \\\n"
extra = "  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=1g,mode=1777 \\\n"

if extra in s:
    print("MOJO CACHE FIX: ALREADY PRESENT")
elif s.count(old) == 1:
    p.write_text(s.replace(old, old + extra))
    print("MOJO CACHE FIX: APPLIED")
else:
    raise SystemExit("STOP: Unexpected launcher format")
PY

bash -n "$CLEAN/run_cta_native.sh" || exit 1
bash "$CLEAN/run_cta_native.sh" check || exit 1

PODMAN=(podman --root "$PODMAN_ROOT" --runroot "$PODMAN_RUNROOT")

if "${PODMAN[@]}" container exists cta-clean-native-batch2; then
  "${PODMAN[@]}" rm -f cta-clean-native-batch2 || exit 1
fi

echo "=== START CORRECTED CLEAN CONTAINER ==="
bash "$CLEAN/run_cta_native.sh" start
