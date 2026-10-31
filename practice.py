podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-batch2-http-20261030 \
  /opt/venv/bin/python -B -c '
from pathlib import Path
import importlib.util
base = Path("/workspace/artifacts/v1.168-max")
required = [
    base / "real_max_batch2_backend.py",
    base / "cta_max/run_batch2_contract.py",
    base / "cta_native_batch2_release_candidate/maxserve_cta_extension/cta_native_launcher.py",
    Path("/workspace/artifacts/v1.168/core-artifact/pipeline.py"),
]
for p in required:
    print(("PASS" if p.is_file() else "MISSING"), p)
assert all(p.is_file() for p in required)
for module in ("max", "torch", "numpy", "faiss"):
    print("MODULE", module, "PRESENT" if importlib.util.find_spec(module) else "MISSING")
print("CLEAN CONTAINER DEPENDENCIES: CHECK COMPLETE")
'
