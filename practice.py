cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1
podman run --rm -i -v "$PWD:/workspace" -w /workspace \
  --entrypoint python docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, inspect
sys.path.insert(0, '/workspace/artifacts/v1.168/utils/dependency-utils')
try:
    from vz_recommender.models.transformer import ParallelTransformerAEP
    print('CLASS FILE:', inspect.getfile(ParallelTransformerAEP))
    print('=== PYTORCH ParallelTransformerAEP.forward ===')
    print(inspect.getsource(ParallelTransformerAEP.forward))
except Exception as e:
    print('SOURCE NOT AVAILABLE:', type(e).__name__, str(e))
    print('NO FILES MODIFIED')
PY
