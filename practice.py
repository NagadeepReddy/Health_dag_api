podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g --cpus=1 \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/triton_repo/rt-aal-upg-leads-v1/1:/aalmodel:ro \
  --entrypoint /bin/sh \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  -c 'id; ls -ld /aalmodel/core-artifact; ls -l /aalmodel/core-artifact/pipeline.py'
