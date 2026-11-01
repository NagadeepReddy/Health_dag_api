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
import torch
from pathlib import Path
from pipeline import pipeline

body = json.loads(Path("/bplan_out/bplan_sanity_features.json").read_text())

model = pipeline()
if not model.loaded:
    model.load()

original_forward = model.bplan_model.forward
captured = {}

def capture_forward(*args, **kwargs):
    if captured:
        raise RuntimeError("Unexpected repeated neural call")
    captured["inputs"] = {
        k: v.detach().cpu().clone() if isinstance(v, torch.Tensor) else v
        for k, v in kwargs.items()
    }
    out = original_forward(*args, **kwargs)
    captured["output"] = out.detach().cpu().clone()
    return out

model.bplan_model.forward = capture_forward
response = model.predict_raw(body)

assert "output" in captured, "Neural inference was not executed"
assert torch.isfinite(captured["output"]).all(), "Non-finite model output"
assert isinstance(response, dict)

torch.save(captured["inputs"], "/bplan_out/bplan_neural_inputs.pt")
torch.save(captured["output"], "/bplan_out/bplan_pytorch_neural_output.pt")

print("BPLAN NEURAL CAPTURE: PASS")
print("INPUT SHAPES:")
for k, v in captured["inputs"].items():
    print(k, tuple(v.shape) if isinstance(v, torch.Tensor) else type(v).__name__)
print("OUTPUT SHAPE:", tuple(captured["output"].shape))
print("OUTPUT FINITE: PASS")
print("NEURAL PARITY FIXTURES SAVED")
PY
