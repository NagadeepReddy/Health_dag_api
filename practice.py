REPO=/application1/sajjna8/rt-pzai-bplan-v1
OUT="$REPO/artifacts/v1.113-max/maxserve_bplan_extension"

podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v "$REPO:/bplan:ro" \
  -v /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031:/cta:ro \
  -v "$OUT:/bplan_out:rw" \
  localhost/cta-max-faiss:local - <<'PY'
import torch, json
from pathlib import Path

b = torch.load("/bplan/artifacts/v1.113/core-artifact/base_model.pt",
               map_location="cpu", weights_only=True)
c = torch.load("/cta/artifacts/v1.168/core-artifact/model_0_base.pt",
               map_location="cpu", weights_only=True)

report = {
    "matching_shapes": [],
    "different_shapes": [],
    "bplan_only": sorted(set(b)-set(c)),
    "cta_only": sorted(set(c)-set(b))
}

for k in sorted(set(b) & set(c)):
    bs, cs = list(b[k].shape), list(c[k].shape)
    if bs == cs:
        report["matching_shapes"].append(k)
    else:
        report["different_shapes"].append({
            "name": k, "cta": cs, "bplan": bs
        })

p = Path("/bplan_out/bplan_cta_weight_mapping.json")
p.write_text(json.dumps(report, indent=2))

print("WEIGHT MAPPING SAVED:", p)
print("MATCHING SHAPES:", len(report["matching_shapes"]))
print("DIFFERENT SHAPES:", len(report["different_shapes"]))
for x in report["different_shapes"]:
    print(x["name"], "CTA", x["cta"], "BPLAN", x["bplan"])
PY
