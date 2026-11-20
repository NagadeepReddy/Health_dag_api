podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g --cpus=1 \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/python:/aalpy:ro \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/encoder:/mnt/all-MiniLM-L6-v2:ro \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/weights:/weights:ro \
  --entrypoint python3 \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  -c 'import sys,torch; sys.path.insert(0,"/aalpy"); from models import RTSMultiLabel; m=RTSMultiLabel(384,3,"/mnt/all-MiniLM-L6-v2",False); s=torch.load("/weights/model_2.pt",map_location="cpu",weights_only=True); m.load_state_dict(s,strict=True); m.eval(); print("MODEL WEIGHTS BIND PASS:",len(s))'
