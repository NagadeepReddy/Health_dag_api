python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
src = base / "nlp_bert_max.py"
dst = base / "nlp_bert_in_graph.py"

assert src.is_file(), "STOP: verified BERT source missing"
assert not dst.exists(), "STOP: reusable adapter already exists"

tree = ast.parse(src.read_text())
functions = [
    n for n in tree.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_nlp_bert_graph"
]
assert len(functions) == 1, "STOP: BERT builder differs"

body = functions[0].body

graph_indices = [
    i for i, n in enumerate(body)
    if isinstance(n, ast.Assign)
    and isinstance(n.value, ast.Call)
    and isinstance(n.value.func, ast.Name)
    and n.value.func.id == "Graph"
]
assert len(graph_indices) == 1, "STOP: graph structure differs"

i = graph_indices[0]
assert isinstance(body[i+1], ast.With), "STOP: graph context differs"
assert isinstance(body[i+2], ast.Return), "STOP: graph return differs"

inside = body[i+1].body
assert ast.unparse(inside[0]) == (
    "ids, attention_mask = graph.inputs"
), "STOP: input binding differs"
assert ast.unparse(inside[-1]) == (
    "graph.output(search)"
), "STOP: graph output differs"

statements = body[:i] + inside[1:-1]

def indent(node):
    return "\n".join(
        "    " + line
        for line in ast.unparse(node).splitlines()
    )

code = (
    "import numpy as np\n"
    "from max.dtype import DType\n"
    "from max.graph import ops\n"
    "from .nlp_bert_max import WEIGHTS\n\n"
    "def nlp_bert_forward(ids, attention_mask, device, seq_len):\n"
    + "\n".join(indent(n) for n in statements)
    + "\n    return search\n"
)

ast.parse(code)
dst.write_text(code)

print("REUSABLE NLP FORWARD CREATED — SYNTAX PASS")
print("VERIFIED SIX-LAYER BERT SOURCE UNCHANGED")
print("ORIGINAL MODEL AND DS CODE UNCHANGED")
PY
