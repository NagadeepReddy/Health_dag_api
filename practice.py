podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
import json
from pathlib import Path
from max.graph import ops

config = json.loads(
    Path("artifacts/v1.168/config/config.json").read_text()
)

print("===== BERT CONFIG =====")
for key in [
    "model_type", "hidden_size", "num_hidden_layers",
    "num_attention_heads", "intermediate_size",
    "hidden_act", "layer_norm_eps",
    "vocab_size", "type_vocab_size",
    "max_position_embeddings"
]:
    print(key, "=", config.get(key))

print("\n===== MAX GRAPH OPERATIONS =====")
for name in [
    "matmul", "softmax", "reshape", "permute",
    "transpose", "gather", "concat", "mean",
    "rsqrt", "relu", "gelu", "tanh",
    "constant", "cast"
]:
    print(name, "=", hasattr(ops, name))

print("\n===== NLP WEIGHT FILES =====")
p = Path("artifacts/v1.168-max/cta_max/nlp_weights")
files = list(p.glob("*.npy"))
print("COUNT:", len(files))
print("ALL 107 PRESENT:", len(files) == 107)

print("\nREAD-ONLY — NO FILES MODIFIED")
PY
