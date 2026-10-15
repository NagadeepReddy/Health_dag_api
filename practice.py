podman run --rm -i --pull=never \
  -v "$PWD:/work:ro" \
  -v /vzwhome/sajjna8:/wheels:ro \
  -w /work \
  --entrypoint /bin/sh \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest -c '
python3 -m pip install --quiet --no-index --no-deps \
  --target /tmp/cta-deps /wheels/faiss_cpu-1.15.1-*.whl &&
PYTHONPATH="/tmp/cta-deps:/work/artifacts/v1.168/core-artifact:/work/artifacts/v1.168-max" \
python3 - <<'"'"'PY'"'"'
from pipeline import pipeline as CTA
from cta_max.live_cta_pipeline_bridge import attach_max

p = CTA()
p.load()
attach_max(p)

print("CTA PIPELINE + MAX BRIDGE: READY")
PY
'
