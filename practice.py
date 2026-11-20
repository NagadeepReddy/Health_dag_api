podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g --cpus=1 \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/python:/aalpy:ro \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/encoder:/mnt/all-MiniLM-L6-v2:ro \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/weights:/weights:ro \
  --entrypoint python3 \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  -c 'import sys,torch; sys.path.insert(0,"/aalpy"); from models import RTSMultiLabel; from transformers import AutoTokenizer; p="/mnt/all-MiniLM-L6-v2"; t=AutoTokenizer.from_pretrained(p,local_files_only=True); x=t("Hello, I have a question about my mobile plan.",return_tensors="pt",truncation=True,max_length=512); m=RTSMultiLabel(384,3,p,False); s=torch.load("/weights/model_2.pt",map_location="cpu",weights_only=True); m.load_state_dict(s,strict=True); m.eval(); torch.set_grad_enabled(False); y=m(x["input_ids"],x["attention_mask"]); print("CPU FORWARD PASS:",tuple(y.shape),bool(torch.isfinite(y).all()))'
