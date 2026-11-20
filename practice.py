podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run -d --name aal-triton-check \
  --pull=never --network=none \
  --memory=4g --cpus=2 --shm-size=512m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e HF_HUB_OFFLINE=1 \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/triton_repo:/models:ro \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/encoder:/mnt/all-MiniLM-L6-v2:ro \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers
