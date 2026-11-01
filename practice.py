ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$ROOT:/bplan:ro" \
  -v /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031:/cta:ro \
  localhost/cta-max-faiss:local - <<'PY'
import json
import numpy as np
import torch
from pathlib import Path

root = Path("/bplan")
mapping = json.loads(
    (root / "bplan_21_weight_resolution.json").read_text()
)["resolved"]

cta = torch.load(
    "/cta/artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True
)

helper_dir = Path("/cta/artifacts/v1.168-max/cta_max")
results = []

for filename, key in sorted(mapping.items()):
    helper = np.load(helper_dir / filename, allow_pickle=False)
    original = cta[key].detach().cpu().numpy()
    bplan = np.load(root / "max_weights" / f"{key}.npy", allow_pickle=False)

    if helper.shape == original.shape:
        layout = "DIRECT"
        reference = original
    elif helper.ndim == 2 and helper.shape == original.T.shape:
        layout = "TRANSPOSE"
        reference = original.T
    else:
        layout = "SHAPE MISMATCH"
        reference = None

    same = reference is not None and np.allclose(
        helper, reference, rtol=1e-5, atol=1e-6
    )

    results.append({
        "file": filename,
        "key": key,
        "layout": layout,
        "cta_values_match": bool(same),
        "cta_helper_shape": list(helper.shape),
        "bplan_source_shape": list(bplan.shape)
    })

out = root / "bplan_21_layout_validation.json"
# Read-only mount: print report instead of writing.
for r in results:
    if r["layout"] == "SHAPE MISMATCH" or not r["cta_values_match"]:
        print(r["layout"], "VALUES_MATCH:", r["cta_values_match"], r["file"])

print("TOTAL:", len(results))
print("SHAPE MISMATCHES:", sum(r["layout"] == "SHAPE MISMATCH" for r in results))
print("VALUE MISMATCHES:", sum(not r["cta_values_match"] for r in results))
print("BPLAN AND CTA ORIGINAL FILES: UNCHANGED")
PY
