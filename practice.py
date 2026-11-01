ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$ROOT:/bplan:ro" \
  -v /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031:/cta:ro \
  localhost/cta-max-faiss:local - <<'PY'
import json, numpy as np, torch
from pathlib import Path

root = Path("/bplan")
mapping = json.loads((root / "bplan_21_weight_resolution.json").read_text())["resolved"]
cta = torch.load("/cta/artifacts/v1.168/core-artifact/model_0_base.pt",
                 map_location="cpu", weights_only=True)

for filename in mapping:
    if not filename.endswith(("seq_dense_bias.npy", "seq_dense_weight.npy")):
        continue

    key = mapping[filename]
    helper = np.load(Path("/cta/artifacts/v1.168-max/cta_max") / filename)
    original = cta[key].numpy()
    bplan = np.load(root / "max_weights" / f"{key}.npy")

    print("\nFILE:", filename)
    print("MAPPED KEY:", key)
    print("CTA HELPER:", helper.shape)
    print("CTA CHECKPOINT:", original.shape)
    print("BPLAN CHECKPOINT:", bplan.shape)
    if helper.shape == original.shape:
        print("CTA DIFFERENCE:", np.max(np.abs(helper - original)))
PY
