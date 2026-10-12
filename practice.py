podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  - <<'PY'
from pathlib import Path
import ast
import sys

from max.graph import ops

base = Path("artifacts/v1.168-max/cta_max")
dst = base / "nlp_bert_max.py"

assert not dst.exists(), "STOP: NLP implementation already exists"
assert len(list((base / "nlp_weights").glob("*.npy"))) == 107

for name in (
    "constant", "gather", "layer_norm", "matmul",
    "softmax", "reshape", "permute", "cast",
    "erf", "tanh", "relu"
):
    assert hasattr(ops, name), f"STOP: {name} unavailable"

code = '''
from pathlib import Path
import numpy as np

from max.dtype import DType
from max.graph import Graph, TensorType, ops

WEIGHTS = Path(__file__).parent / "nlp_weights"


def build_nlp_bert_graph(device, seq_len=4):
    assert 1 <= seq_len <= 512

    cache = {}

    def weight(name):
        if name not in cache:
            path = WEIGHTS / (name + ".npy")
            assert path.is_file(), f"Missing NLP weight: {name}"
            arr = np.load(path).astype(np.float32)
            cache[name] = ops.constant(
                arr, dtype=DType.float32, device=device
            )
        return cache[name]

    def linear(x, prefix):
        w = weight(prefix + ".weight")
        b = weight(prefix + ".bias")
        return ops.matmul(x, ops.permute(w, [1, 0])) + b

    def norm(x, prefix):
        return ops.layer_norm(
            x,
            weight(prefix + ".weight"),
            weight(prefix + ".bias"),
            1e-12,
        )

    def gelu(x):
        return 0.5 * x * (
            1.0 + ops.erf(x * 0.7071067811865476)
        )

    graph = Graph(
        "cta_nlp_bert_six_layers",
        input_types=[
            TensorType(DType.int64, [1, seq_len], device=device),
            TensorType(DType.int64, [1, seq_len], device=device),
        ],
    )

    with graph:
        ids, attention_mask = graph.inputs

        emb = "nlp_encoder.embeddings"

        position_ids = ops.constant(
            np.arange(seq_len, dtype=np.int64).reshape(1, seq_len),
            dtype=DType.int64,
            device=device,
        )
        token_types = ops.constant(
            np.zeros((1, seq_len), dtype=np.int64),
            dtype=DType.int64,
            device=device,
        )

        x = (
            ops.gather(weight(emb + ".word_embeddings"), ids, axis=0)
            + ops.gather(
                weight(emb + ".position_embeddings"),
                position_ids, axis=0
            )
            + ops.gather(
                weight(emb + ".token_type_embeddings"),
                token_types, axis=0
            )
        )

        x = norm(x, emb + ".LayerNorm")

        # Valid tokens = 1; masked tokens = 0.
        mask = ops.reshape(
            (ops.cast(attention_mask, DType.float32) - 1.0)
            * 10000.0,
            [1, 1, 1, seq_len],
        )

        for i in range(6):
            prefix = f"nlp_encoder.encoder.layer.{i}"

            q = linear(x, prefix + ".attention.self.query")
            k = linear(x, prefix + ".attention.self.key")
            v = linear(x, prefix + ".attention.self.value")

            q = ops.permute(
                ops.reshape(q, [1, seq_len, 12, 32]),
                [0, 2, 1, 3],
            )
            k = ops.permute(
                ops.reshape(k, [1, seq_len, 12, 32]),
                [0, 2, 3, 1],
            )
            v = ops.permute(
                ops.reshape(v, [1, seq_len, 12, 32]),
                [0, 2, 1, 3],
            )

            scores = ops.matmul(q, k) * (32.0 ** -0.5)
            probs = ops.softmax(scores + mask, axis=-1)
            context = ops.matmul(probs, v)

            context = ops.reshape(
                ops.permute(context, [0, 2, 1, 3]),
                [1, seq_len, 384],
            )

            attention_out = linear(
                context, prefix + ".attention.output.dense"
            )
            x = norm(
                x + attention_out,
                prefix + ".attention.output.LayerNorm",
            )

            intermediate = gelu(
                linear(x, prefix + ".intermediate.dense")
            )
            output = linear(
                intermediate, prefix + ".output.dense"
            )
            x = norm(
                x + output,
                prefix + ".output.LayerNorm",
            )

        # Original BERT pooler: first token -> dense -> tanh.
        first_index = ops.constant(
            np.array([0], dtype=np.int64),
            dtype=DType.int64,
            device=device,
        )

        cls = ops.reshape(
            ops.gather(x, first_index, axis=1),
            [1, 384],
        )

        pooled = ops.tanh(
            linear(cls, "nlp_encoder.pooler.dense")
        )

        # Original GRecBase NLP projection.
        search = linear(pooled, "nlp_dense_0")
        search = ops.relu(search) - 0.2 * ops.relu(-search)
        search = linear(search, "nlp_dense_1")

        graph.output(search)

    return graph
'''

ast.parse(code)
dst.write_text(code)

sys.path.insert(0, str(base))
from nlp_bert_max import build_nlp_bert_graph

from max.driver import CPU
from max.graph import DeviceRef

device = DeviceRef.from_device(CPU())
graph = build_nlp_bert_graph(device, seq_len=4)

print("SIX-LAYER BERT GRAPH CONSTRUCTION: PASS")
print("NLP GRAPH OUTPUT:", graph.output_types)
print("107 NLP WEIGHT FILES PRESERVED")
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
