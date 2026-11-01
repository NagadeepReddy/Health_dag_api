REPO=/application1/sajjna8/rt-pzai-bplan-v1
ROOT="$REPO/artifacts/v1.113-max/maxserve_bplan_extension"

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$ROOT:/bplan_out:rw" \
  -v /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031:/cta:ro \
  localhost/cta-max-faiss:local - <<'PY'
import json
import numpy as np
import torch
from pathlib import Path

root = Path("/bplan_out")
mapping = json.loads(
    (root / "bplan_21_weight_resolution.json").read_text()
)["resolved"]

cta = torch.load(
    "/cta/artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu",
    weights_only=True
)

cta_helpers = Path("/cta/artifacts/v1.168-max/cta_max")
destination = root / "bplan_weight_layout"

validated = []

for filename, key in sorted(mapping.items()):
    source = cta_helpers / filename
    bplan_source = root / "max_weights" / f"{key}.npy"

    assert source.is_file(), f"CTA helper missing: {filename}"
    assert key in cta, f"CTA tensor missing: {key}"
    assert bplan_source.is_file(), f"BPLAN tensor missing: {key}"

    helper = np.load(source, allow_pickle=False)
    original = cta[key].detach().cpu().numpy()
    bplan = np.load(bplan_source, allow_pickle=False)

    if helper.shape == original.shape and np.allclose(helper, original, rtol=1e-5, atol=1e-6):
        converted = bplan
    elif helper.shape == original.T.shape and np.allclose(helper, original.T, rtol=1e-5, atol=1e-6):
        converted = bplan.T
    else:
        raise RuntimeError(
            f"STOP: unverified weight transformation: {filename}"
        )

    validated.append((filename, converted.copy()))

for filename, array in validated:
    target = destination / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    np.save(target, array, allow_pickle=False)

print("BPLAN VALIDATED WEIGHT EXPORT: PASS")
print("WEIGHTS:", len(validated))
print("LOCATION:", destination)
print("ORIGINAL BPLAN DS AND CTA: UNCHANGED")
PY
