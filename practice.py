REPO=/application1/sajjna8/rt-pzai-bplan-v1
OUT="$REPO/artifacts/v1.113-max/maxserve_bplan_extension"

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:/workspace:ro" \
  -v "$OUT:/bplan_out:rw" \
  -w /workspace/artifacts/v1.113/core-artifact \
  localhost/cta-max-faiss:local - <<'PY'
import json
import numpy as np
import torch
from pathlib import Path
from pipeline import pipeline

body = json.loads(Path("/bplan_out/bplan_sanity_features.json").read_text())
model = pipeline()
model.load()

captured = []

def capture_projection(module, inputs):
    captured.append(inputs[0].detach().cpu().numpy().copy())

hook = model.bplan_model.dense1.register_forward_pre_hook(capture_projection)

try:
    result = model.predict_raw(body)
finally:
    hook.remove()

assert len(captured) == 1, f"Expected one projection call, got {len(captured)}"

x = captured[0]
w = model.bplan_model.dense1.weight.detach().cpu().numpy().copy()
reference = torch.load(
    "/bplan_out/bplan_pytorch_neural_output.pt",
    map_location="cpu", weights_only=True
).numpy()

assert x.shape == (1, 2048), x.shape
assert w.shape == (10438, 2048), w.shape
assert reference.shape == (1, 10438), reference.shape

np.save("/bplan_out/bplan_transfer_input.npy", x)
np.save("/bplan_out/bplan_transfer_weight.npy", w)
np.save("/bplan_out/bplan_transfer_reference.npy", reference)

print("BPLAN TRANSFER FIXTURES: PASS")
print("INPUT:", x.shape)
print("WEIGHT:", w.shape)
print("REFERENCE:", reference.shape)
print("SAVED FOR MAX PROJECTION PARITY")
PY
