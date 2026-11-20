podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g --cpus=1 \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/encoder:/mnt/all-MiniLM-L6-v2:ro \
  --entrypoint python3 \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  -c 'from transformers import AutoTokenizer; t=AutoTokenizer.from_pretrained("/mnt/all-MiniLM-L6-v2",local_files_only=True); print("NONROOT TOKENIZER PASS:",t.__class__.__name__,t.vocab_size)'
