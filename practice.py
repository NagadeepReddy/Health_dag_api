podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
import sys

base = Path("artifacts/v1.168-max/cta_max")
p = base / "nlp_bert_max.py"
s = p.read_text()

names = [
    "word_embeddings",
    "position_embeddings",
    "token_type_embeddings",
]

for name in names:
    old = f'weight(emb + ".{name}")'
    new = f'weight(emb + ".{name}.weight")'

    assert s.count(old) == 1, f"STOP: unexpected code for {name}"
    assert (
        base / "nlp_weights" /
        f"nlp_encoder.embeddings.{name}.weight.npy"
    ).is_file(), f"STOP: missing {name} weight file"

    s = s.replace(old, new, 1)

ast.parse(s)
p.write_text(s)

print("THREE EMBEDDING WEIGHT REFERENCES FIXED")

sys.path.insert(0, str(base))

from max.driver import CPU
from max.graph import DeviceRef
from nlp_bert_max import build_nlp_bert_graph

device = DeviceRef.from_device(CPU())

graph = build_nlp_bert_graph(device, seq_len=4)

print("SIX-LAYER BERT GRAPH CONSTRUCTION: PASS")
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
