podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  -v /application1/sajjna8/rt-pzai-bplan-v1:/workspace:ro \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -c 'import torch
p="/workspace/artifacts/v1.113/core-artifact/bplan_model.pt"
s=torch.load(p,map_location="cpu",weights_only=True)
if "state_dict" in s: s=s["state_dict"]
print("TOTAL TENSORS:",len(s))
for k,v in list(s.items())[:80]:
    print(k,tuple(v.shape) if hasattr(v,"shape") else type(v).__name__)'
