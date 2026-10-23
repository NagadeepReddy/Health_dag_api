cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=8g --pids-limit=32 \
  -v "$PWD:/workspace:ro" \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -c '
import sys
sys.path.insert(0, "/workspace/artifacts/v1.168/core-artifact")

from pipeline import pipeline as CTA

p = CTA()
print("REAL CTA INSTANCE: PASS", flush=True)
print("LOAD:", callable(getattr(p, "load", None)), flush=True)
print("PREDICT_RAW:", callable(getattr(p, "predict_raw", None)), flush=True)
'

echo "EXIT CODE: $?"
