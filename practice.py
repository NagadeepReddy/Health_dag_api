python - <<'PY'
from pathlib import Path
import ast
import re

p = Path("artifacts/v1.168-max/cta_max/sequence_postprocess_max.py")
s = p.read_text()

pattern = r'ops\.unsqueeze\(\s*ops\.mean\(x\s*\*\s*x,\s*axis=-1\),\s*axis=-1\s*\)'

updated, count = re.subn(
    pattern,
    "ops.mean(x * x, axis=-1)",
    s
)

assert count == 2, f"STOP: Expected 2 corrections, found {count}"

ast.parse(updated)
p.write_text(updated)

print("BOTH NORMALIZATION SHAPES CORRECTED")
print("SYNTAX OK")
print("ORIGINAL TRANSFORMER AND DS CODE UNCHANGED")
PY

if [ $? -eq 0 ]; then
  podman run --rm -i \
    -v "$PWD:/workspace" -w /workspace \
    --entrypoint python \
    docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
    artifacts/v1.168-max/cta_max/run_transformer_sequence.py

  python - <<'PY'
import numpy as np

p = "artifacts/v1.168-max/cta_max/sequence_combined_output.npy"
out = np.load(p)

print("COMBINED OUTPUT SHAPE:", out.shape)
print("FINITE:", bool(np.isfinite(out).all()))
print("INTEGRATION PASS:", out.shape == (1, 256) and np.isfinite(out).all())
PY
fi
