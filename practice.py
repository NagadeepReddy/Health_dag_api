podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g --cpus=1 \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e HF_HUB_OFFLINE=1 \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/triton_repo/rt-aal-upg-leads-v1/1:/aalmodel:ro \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/encoder:/mnt/all-MiniLM-L6-v2:ro \
  --entrypoint python3 \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  -c 'import sys; sys.path.insert(0,"/aalmodel/core-artifact"); sys.path.insert(0,"/aalmodel/utils/dependency-utils"); from pipeline import pipeline; p=pipeline(); p.load(); print("AAL PIPELINE LOAD PASS")'
