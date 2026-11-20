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
  -c '
import sys, json, torch
sys.path.insert(0, "/aalpy")
from models import RTSMultiLabel
from transformers import AutoTokenizer

p = "/mnt/all-MiniLM-L6-v2"
names = ["AAL", "UPG", "No_purchase"]
t = AutoTokenizer.from_pretrained(p, local_files_only=True)
m = RTSMultiLabel(384, 3, p, False)
s = torch.load("/weights/model_2.pt", map_location="cpu", weights_only=True)
m.load_state_dict(s, strict=True)
m.eval()

ref = json.load(open("/input/sanity_output.json"))["prediction"]
expected = [float(ref[n]["score_value"]) for n in names]
print("REFERENCE:", expected)

with torch.inference_mode():
    for i in (1, 2, 3):
        data = json.load(open(f"/input/load_input_{i}.json"))
        x = t(data["transcript"], return_tensors="pt",
              truncation=True, max_length=512)
        y = torch.sigmoid(m(x["input_ids"], x["attention_mask"]))
        scores = y[0].tolist()
        diffs = [abs(a-b) for a,b in zip(scores, expected)]
        print(f"INPUT {i}: scores={scores} max_diff={max(diffs):.8f}")
'
