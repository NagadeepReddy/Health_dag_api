python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
src = base / "run_transformer_2layers.py"
dst = base / "run_transformer_sequence.py"

assert src.is_file()
assert (base / "parallel_transformer_graph_sequence.py").is_file()
assert not dst.exists(), "STOP: combined runner already exists"

s = src.read_text()

old = "from parallel_transformer_graph_2layers import build_parallel_transformer_graph"
new = "from parallel_transformer_graph_sequence import build_parallel_transformer_graph"
assert s.count(old) == 1, "STOP: original graph import differs"

s = s.replace(old, new, 1)

# Make the cta_max package importable.
s = (
    'import sys\n'
    'sys.path.insert(0, "artifacts/v1.168-max")\n'
    + s
)

# Add dense weights to the existing proven WeightData loading loops.
marker = "weights = {}"
assert s.count(marker) >= 1, "STOP: weight registry differs"

addition = '''
weight_files.update({
    "sequence_transformer.seq_dense.weight":
        "artifacts/v1.168-max/cta_max/sequence_weights/seq_dense_weight.npy",
    "sequence_transformer.seq_dense.bias":
        "artifacts/v1.168-max/cta_max/sequence_weights/seq_dense_bias.npy",
})
weights = {}
'''
s = s.replace(marker, addition)

# Protect the saved transformer-only parity output.
old_output = "transformer_max_output_2layers.npy"
assert s.count(old_output) == 1, "STOP: transformer output handling differs"
s = s.replace(old_output, "sequence_combined_output.npy")

ast.parse(s)
dst.write_text(s)

print("COMBINED SEQUENCE RUNNER CREATED")
print("ORIGINAL TRANSFORMER RUNNER UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_transformer_sequence.py
