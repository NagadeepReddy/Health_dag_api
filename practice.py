python - <<'PY'
from pathlib import Path
import ast

b = Path("artifacts/v1.168-max/cta_max")
src = b / "parallel_transformer_graph_2layers.py"
dst = b / "parallel_transformer_graph_sequence.py"

assert src.is_file()
assert (b / "sequence_postprocess_max.py").is_file()
assert not dst.exists(), "STOP: sequence graph already exists"

s = src.read_text()

old_import = (
    "from parallel_transformer_block_2layers "
    "import ParallelTransformerBlockMAX"
)

assert s.count(old_import) == 1, "STOP: block import differs"
assert s.count("graph.output(output)") == 1, "STOP: graph output differs"

s = s.replace(
    old_import,
    old_import + "\nfrom cta_max.sequence_postprocess_max import SequencePostprocessMAX",
    1
)

lines = s.splitlines()

matches = [
    i for i, line in enumerate(lines)
    if line.strip() == "graph = Graph("
]

assert len(matches) == 1, "STOP: graph construction differs"

i = matches[0]
indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]

lines.insert(
    i,
    indent + "postprocess = SequencePostprocessMAX("
    "dtype=DType.float32, device=device_ref)"
)

s = "\n".join(lines) + "\n"
s = s.replace(
    "graph.output(output)",
    "graph.output(postprocess(output))",
    1
)

ast.parse(s)
dst.write_text(s)

print("COMBINED SEQUENCE GRAPH CREATED — SYNTAX OK")
print("TWO-LAYER GRAPH AND DS CODE UNCHANGED")
PY
