python - <<'PY'
import ast
from pathlib import Path

p = Path(
    "artifacts/v1.168-max/cta_max/"
    "parallel_transformer_graph_full_sequence.py"
)

assert p.is_file(), "STOP: full sequence graph missing"

source = p.read_text()
tree = ast.parse(source)

matches = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_parallel_transformer_graph"
]

assert len(matches) == 1, "STOP: graph builder differs"

print("===== EXISTING FULL SEQUENCE GRAPH =====")
print(ast.get_source_segment(source, matches[0]))
print("===== END =====")
print("NO FILES MODIFIED")
PY
