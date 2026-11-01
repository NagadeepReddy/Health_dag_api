ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$ROOT:/bplan:ro" \
  -v /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031:/cta:ro \
  localhost/cta-max-faiss:local - <<'PY'
import numpy as np
import torch

name = "seq_dense.bias"

helper = np.load(
    "/cta/artifacts/v1.168-max/cta_max/grecbase_integration_weights/seq_dense_bias.npy"
)
checkpoint = torch.load(
    "/cta/artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)[name].numpy()
bplan = np.load(f"/bplan/max_weights/{name}.npy")

print("CTA HELPER:", helper.shape, helper.dtype)
print("CTA CHECKPOINT:", checkpoint.shape, checkpoint.dtype)
print("BPLAN WEIGHT:", bplan.shape, bplan.dtype)

if helper.shape == checkpoint.shape:
    print("CTA MAX DIFFERENCE:", np.max(np.abs(helper - checkpoint)))
    print("EXACT MATCH:", np.array_equal(helper, checkpoint))
    print("ALLCLOSE:", np.allclose(helper, checkpoint, rtol=1e-5, atol=1e-6))

print("CTA HELPER SAMPLE:", helper.flatten()[:5])
print("CTA CHECKPOINT SAMPLE:", checkpoint.flatten()[:5])
PY
