cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

timeout -k 5s 45s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never \
  --network=none --memory=6g --cpus=2 --pids-limit=32 \
  -v "$PWD:/workspace:ro" \
  -w /workspace/artifacts/v1.168/core-artifact \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -c '
from pipeline import pipeline
print("STARTING REAL CTA MODEL LOAD", flush=True)
p = pipeline()
p.load()
print("REAL CTA MODEL LOAD: PASS", flush=True)
'

echo "EXIT CODE: $?"
