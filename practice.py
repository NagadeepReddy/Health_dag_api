podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm --pull=never --network=none \
  --memory=2g --cpus=1 \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/python:/aalpy:ro \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/encoder:/mnt/all-MiniLM-L6-v2:ro \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/weights:/weights:ro \
  -v /application1/sajjna8/tfy_triton_work/aal_triton_stage/input:/input:ro \
  --entrypoint python3 \
  ienv-docker-np.oneartifactoryci.verizon.com/jarvis/nvidia/tritonserver:rt-cta-offers \
  -c 'import sys,json,torch; sys.path.insert(0,"/aalpy"); from models import RTSMultiLabel; from transformers import AutoTokenizer; p="/mnt/all-MiniLM-L6-v2"; t=AutoTokenizer.from_pretrained(p,local_files_only=True); text=json.load(open("/input/load_input_3.json"))["transcript"]; x=t(text,return_tensors="pt",truncation=True,max_length=512); m=RTSMultiLabel(384,3,p,False); m.load_state_dict(torch.load("/weights/model_2.pt",map_location="cpu",weights_only=True),strict=True); m.eval(); torch.set_grad_enabled(False); y=torch.sigmoid(m(x["input_ids"],x["attention_mask"])); print("REAL SAMPLE FORWARD PASS:",tuple(y.shape),bool(torch.isfinite(y).all())); print("AAL, UPG, No_purchase:",y[0].tolist())'
