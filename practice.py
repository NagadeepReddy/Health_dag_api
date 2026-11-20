podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g --cpus=1 \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/weights:/weights:ro \
  --entrypoint python3 \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  -c 'import torch; s=torch.load("/weights/model_2.pt",map_location="cpu",weights_only=True); print("CHECKPOINT LOAD PASS:",type(s).__name__,len(s))'
