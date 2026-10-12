podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest - <<'PY'
import sys, ast, re
from pathlib import Path
import numpy as np

sys.path.insert(0, "/workspace/artifacts/v1.168-max")

from max.driver import CPU, Tensor
from max.engine import InferenceSession
from max.graph import DeviceRef
from max.graph.weights import WeightData

base = Path("artifacts/v1.168-max/cta_max")
original = base / "grecbase_fusion_with_context_max.py"
target = base / "grecbase_fusion_with_nlp_max.py"
models = Path("artifacts/v1.168/utils/dependency-utils/models.py")

source = original.read_text()
nlp_source = (base / "nlp_bert_in_graph.py").read_text()

assert "def nlp_bert_forward(" in nlp_source
assert "return search" in nlp_source

# Match the original PyTorch final NLP activation.
activation = re.findall(
    r"self\.nlp_act1\s*=\s*(.+)", models.read_text()
)
assert len(activation) == 1, activation

act = activation[0].strip()
print("ORIGINAL NLP ACT1:", act)

if "LeakyReLU" in act:
    slope = re.search(r"LeakyReLU\(\s*([0-9.]+)", act)
    assert slope, "Cannot verify LeakyReLU slope"
    a = float(slope.group(1))
    act_code = f"search = ops.relu(search) - {a} * ops.relu(-search)"
elif "ReLU(" in act:
    act_code = "search = ops.relu(search)"
elif "Identity(" in act:
    act_code = "pass"
elif "SiLU(" in act:
    act_code = "search = search * ops.sigmoid(search)"
else:
    raise RuntimeError(
        "Unrecognized original activation; no files changed: " + act
    )

def change(old, new):
    global source
    assert source.count(old) == 1, (
        "Existing graph differs; no files changed: " + old[:80]
    )
    source = source.replace(old, new)

change(
    "from cta_max.main_context_max import main_context_forward",
    "from cta_max.main_context_max import main_context_forward\n"
    "from cta_max.nlp_bert_in_graph import nlp_bert_forward"
)

change(
    "def build_grecbase_fusion_graph_with_context(device):",
    "def build_grecbase_fusion_graph_with_nlp(device):"
)

# Sequence and sibling remain external for now.
change("for _ in range(4)]", "for _ in range(2)]")

change(
    "[TensorType(DType.float32, [1, 127], device=device)]",
    "[TensorType(DType.float32, [1, 127], device=device)]"
    " + [TensorType(DType.int64, [1, 8], device=device)"
    " for _ in range(2)]"
)

change(
    "seq, search0, search1, sibling, task0, task1, ihq_ids, jet_name, jet_status, *context_inputs = graph.inputs",
    """seq, sibling, task0, task1, ihq_ids, jet_name, jet_status, *remaining = graph.inputs
        assert len(remaining) == 20
        context_inputs = remaining[:18]
        input_ids, attention_mask = remaining[18:]"""
)

change(
    "assert len(context_inputs) == 18",
    """assert len(context_inputs) == 18

        search = nlp_bert_forward(
            input_ids, attention_mask, device, 8
        )
        """ + act_code + """

        idx0 = ops.constant(
            np.arange(256, dtype=np.int64),
            dtype=DType.int64, device=device
        )
        idx1 = ops.constant(
            np.arange(256, 512, dtype=np.int64),
            dtype=DType.int64, device=device
        )
        search0 = ops.gather(search, idx0, axis=1)
        search1 = ops.gather(search, idx1, axis=1)"""
)

ast.parse(source)

if target.exists():
    assert target.read_text() == source, (
        "Target already exists with different content; not overwritten"
    )
else:
    target.write_text(source)

print("NLP INTEGRATION FILE: READY")

from cta_max.grecbase_fusion_with_nlp_max import (
    build_grecbase_fusion_graph_with_nlp
)

weights = {}
for p in sorted(base.rglob("att_pooling.*.npy")):
    arr = np.load(p).astype(np.float32)
    assert p.stem not in weights
    weights[p.stem] = WeightData.from_numpy(arr, p.stem)

device = CPU()
graph = build_grecbase_fusion_graph_with_nlp(DeviceRef.CPU())
session = InferenceSession(devices=[device])
model = session.load(graph, weights_registry=weights)

print("NLP + CONTEXT + AUX COMPILATION: PASS")

def tensor(shape, dtype):
    return Tensor.from_numpy(
        np.zeros(shape, dtype=dtype)
    ).to(device)

inputs = [
    tensor((1, 256), np.float32)
    for _ in range(2)
]
inputs += [
    tensor((1,), np.int64)
    for _ in range(2)
]
inputs += [
    tensor((1, 1), np.int64)
    for _ in range(3)
]
inputs += [
    tensor((1,), np.int64)
    for _ in range(17)
]
inputs.append(tensor((1, 127), np.float32))

inputs.append(tensor((1, 8), np.int64))
inputs.append(
    Tensor.from_numpy(
        np.ones((1, 8), dtype=np.int64)
    ).to(device)
)

result = model.execute(*inputs)[0].to_numpy()

print("OUTPUT SHAPE:", result.shape)
print("FINITE:", bool(np.isfinite(result).all()))

assert result.shape == (1, 10819), result.shape
assert np.isfinite(result).all()

print("SIX GRECBASE BRANCHES CONNECTED: PASS")
print("ORIGINAL PYTORCH AND DS CODE UNCHANGED")
PY
