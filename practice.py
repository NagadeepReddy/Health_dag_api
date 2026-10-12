podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import sys
import numpy as np
import torch
import torch.nn.functional as F
from pathlib import Path

from max.driver import CPU
from max.graph import DeviceRef
from max.engine import InferenceSession

sys.path.insert(0, "artifacts/v1.168-max/cta_max")
from nlp_bert_max import build_nlp_bert_graph

try:
    from transformers import BertConfig, BertModel
except Exception as e:
    raise SystemExit(
        f"STOP: PyTorch BERT reference unavailable: {e}"
    )

base = Path("artifacts/v1.168-max/cta_max/nlp_weights")
config_path = "artifacts/v1.168/config/config.json"

files = sorted(base.glob("*.npy"))
assert len(files) == 107, f"STOP: {len(files)} weights"

weights = {
    p.stem: torch.from_numpy(np.load(p).astype(np.float32))
    for p in files
}

config = BertConfig.from_json_file(config_path)
bert = BertModel(config)

bert_weights = {
    k.removeprefix("nlp_encoder."): v
    for k, v in weights.items()
    if k.startswith("nlp_encoder.")
}

missing, unexpected = bert.load_state_dict(
    bert_weights, strict=False
)

allowed_missing = {
    "embeddings.position_ids",
    "embeddings.token_type_ids",
}

assert set(missing) <= allowed_missing, (
    f"STOP: missing BERT weights: {missing}"
)
assert not unexpected, (
    f"STOP: unexpected BERT weights: {unexpected}"
)

bert.eval()

ids = np.array([[101, 2023, 2003, 102]], dtype=np.int64)
mask = np.array([[1, 1, 1, 1]], dtype=np.int64)

with torch.inference_mode():
    pooled = bert(
        input_ids=torch.from_numpy(ids),
        attention_mask=torch.from_numpy(mask),
    ).pooler_output

    x = F.linear(
        pooled,
        weights["nlp_dense_0.weight"],
        weights["nlp_dense_0.bias"],
    )
    x = F.leaky_relu(x, negative_slope=0.2)
    x = F.linear(
        x,
        weights["nlp_dense_1.weight"],
        weights["nlp_dense_1.bias"],
    )
    pt_out = x.numpy()

cpu = CPU()
device = DeviceRef.from_device(cpu)

graph = build_nlp_bert_graph(device, seq_len=4)
session = InferenceSession(devices=[cpu])
model = session.load(graph)

max_out = model.execute(ids, mask)[0].to_numpy()

print("PYTORCH SHAPE:", pt_out.shape)
print("MAX SHAPE:", max_out.shape)
print("MAX DIFF:", np.max(np.abs(pt_out - max_out)))
print("MATCH:", np.allclose(
    pt_out, max_out, rtol=1e-4, atol=1e-5
))
print("BOTH FINITE:", bool(
    np.isfinite(pt_out).all() and np.isfinite(max_out).all()
))
PY
