
podman run --rm \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  -c '
import sys
import pickle
sys.path.insert(0, "artifacts/v1.168-max")

from max.interfaces.context import BaseContext, GenerationStatus
from maxserve_cta_extension.cta_context import CTAContext

ctx = CTAContext("cta-check-001", {"offers": []})

assert isinstance(ctx, BaseContext)
assert ctx.request_id == "cta-check-001"
assert ctx.status == GenerationStatus.ACTIVE
assert ctx.body == {"offers": []}

restored = pickle.loads(pickle.dumps(ctx))
assert restored.request_id == ctx.request_id
assert restored.body == ctx.body

ctx.status = GenerationStatus.END_OF_SEQUENCE
assert ctx.is_done

print("CTA NATIVE CONTEXT RUNTIME: PASS")
print("MAX BASE CONTEXT: PASS")
print("SERIALIZATION: PASS")
print("STATUS LIFECYCLE: PASS")
'
