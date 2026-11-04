cd /application1/sajjna8/rt-pzaas-v1.0 && bash <<'SH'
ROOT=/application1/podman/storage
RUN=/run/containers/storage

echo "=== EXISTING MODEL RUNTIME DEPENDENCIES ==="

podman --root "$ROOT" --runroot "$RUN" \
  images --format '{{.Repository}}:{{.Tag}}' |
grep -E 'cta-max-faiss:local|modular/max-full:latest|tritonserver:24.09-py3' |
sort -u | head -5 |
while IFS= read -r img; do
  echo "=== IMAGE: $img ==="

  podman --root "$ROOT" --runroot "$RUN" \
    run --rm --pull=never --network none \
    --memory 2g --entrypoint /bin/sh "$img" -c '
python3 - <<PY
import importlib.util

for name in [
    "torch", "max", "einops",
    "apscheduler", "transformers",
    "faiss", "sklearn", "joblib"
]:
    try:
        found = importlib.util.find_spec(name)
        print(name, "AVAILABLE" if found else "MISSING")
    except Exception:
        print(name, "MISSING")
PY
' 2>&1 | tail -14
done

echo "RUNTIME DEPENDENCY CHECK: COMPLETE"
echo "ORIGINAL DS: UNCHANGED"
SH
