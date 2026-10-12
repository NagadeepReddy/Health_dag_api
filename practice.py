python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
src = base / "run_transformer_sequence.py"
dst = base / "run_transformer_full_sequence.py"

assert src.is_file(), "STOP: working runner missing"
assert (base / "parallel_transformer_graph_full_sequence.py").is_file()
assert not dst.exists(), "STOP: full runner already exists"

s = src.read_text()

old_import = (
    "from parallel_transformer_graph_sequence "
    "import build_parallel_transformer_graph"
)
new_import = (
    "from parallel_transformer_graph_full_sequence "
    "import build_parallel_transformer_graph"
)

assert s.count(old_import) == 1, "STOP: graph import differs"
assert s.count("weights = {}") == 1, "STOP: weight registry differs"
assert s.count("model.execute(x, pos)") == 1, "STOP: execution differs"
assert s.count("sequence_combined_output.npy") == 1, "STOP: output differs"

s = s.replace(old_import, new_import, 1)

extra_weights = '''
weight_files.update({
    "sequence_transformer.page_embedding":
        "artifacts/v1.168-max/cta_max/sequence_weights/page_embedding_weight.npy",
    "sequence_transformer.item_embedding":
        "artifacts/v1.168-max/cta_max/sequence_weights/item_embedding_weight.npy",
    "sequence_transformer.item_meta_embedding":
        "artifacts/v1.168-max/cta_max/sequence_weights/item_meta_embedding_weight.npy",
    "sequence_transformer.item_pre_embedding":
        "artifacts/v1.168-max/cta_max/sequence_weights/item_pre_embedding_weight.npy",
    "sequence_transformer.page_meta_wide_dense.weight":
        "artifacts/v1.168-max/cta_max/sequence_weights/page_meta_wide_dense_weight.npy",
    "sequence_transformer.page_meta_wide_dense.bias":
        "artifacts/v1.168-max/cta_max/sequence_weights/page_meta_wide_dense_bias.npy",
})
weights = {}
'''

s = s.replace("weights = {}", extra_weights, 1)

inputs = '''
page = np.array([[1, 2, 3, 4]], dtype=np.int64)
item = np.array([[10, 20, 30, 40]], dtype=np.int64)
meta = np.array([[1, 2, 3, 4]], dtype=np.int64)
wide = np.array(
    [[[0.1], [0.2], [-0.3], [0.4]]],
    dtype=np.float32
)

assert pos.shape == (1, 1, 4, 256), (
    f"STOP: rotary position shape {pos.shape}"
)

out = model.execute(page, item, meta, wide, pos)[0]
'''

s = s.replace("out = model.execute(x, pos)[0]", inputs, 1)
s = s.replace(
    "sequence_combined_output.npy",
    "sequence_real_full_output.npy",
    1
)

ast.parse(s)
dst.write_text(s)

print("FULL SEQUENCE RUNNER CREATED")
print("ORIGINAL RUNNERS AND DS CODE UNCHANGED")
PY

if [ $? -eq 0 ]; then
  podman run --rm -i \
    -v "$PWD:/workspace" -w /workspace \
    --entrypoint python \
    docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
    artifacts/v1.168-max/cta_max/run_transformer_full_sequence.py
fi
