podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g --cpus=1 --user 0 \
  -v /application1/sajjna8/tfy_triton_work/rt-aal-upg-lead-v1/artifacts/v1.4/config:/mnt/all-MiniLM-L6-v2:ro \
  --entrypoint python3 \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  -c 'from transformers import AutoConfig; c=AutoConfig.from_pretrained("/mnt/all-MiniLM-L6-v2",local_files_only=True); print("ENCODER CONFIG PASS:",c.model_type,c.hidden_size)'
