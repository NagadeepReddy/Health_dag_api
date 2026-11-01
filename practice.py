podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --entrypoint python3 \
  -v /application1/sajjna8/rt-pzai-bplan-v1:/bplan:ro \
  -v /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031:/cta:ro \
  localhost/cta-max-faiss:local - <<'PY'
import torch

b = torch.load(
    "/bplan/artifacts/v1.113/core-artifact/base_model.pt",
    map_location="cpu", weights_only=True
)
c = torch.load(
    "/cta/artifacts/v1.168/core-artifact/model_0_base.pt",
    map_location="cpu", weights_only=True
)

bk, ck = set(b), set(c)
shared = bk & ck
same = [k for k in shared if tuple(b[k].shape) == tuple(c[k].shape)]
different = [k for k in shared if tuple(b[k].shape) != tuple(c[k].shape)]

print("BPLAN TENSORS:", len(b))
print("CTA TENSORS:", len(c))
print("MATCHING NAMES:", len(shared))
print("MATCHING SHAPES:", len(same))
print("DIFFERENT SHAPES:", len(different))
print("BPLAN-ONLY:", len(bk - ck))
print("CTA-ONLY:", len(ck - bk))

for k in sorted(different)[:20]:
    print("SHAPE MISMATCH:", k, tuple(c[k].shape), "->", tuple(b[k].shape))

for k in sorted(bk - ck)[:20]:
    print("BPLAN-ONLY:", k)

for k in sorted(ck - bk)[:20]:
    print("CTA-ONLY:", k)
PY
