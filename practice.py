podman --root /application1/podman/storage --runroot /run/containers/storage run --rm --pull=never --network=none \
-v /application1/sajjna8/rt-pzai-bplan-v1:/workspace:ro \
--entrypoint /opt/venv/bin/python localhost/cta-max-faiss:local \
-c 'import torch; p="/workspace/artifacts/v1.113/core-artifact/base_model.pt"; s=torch.load(p,map_location="cpu",weights_only=True); s=s.get("state_dict",s); print("\n".join(f"{k}: {tuple(v.shape)}" for k,v in s.items() if "norm1_g" in k))'
