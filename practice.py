cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import os

repo = Path.cwd()
base = Path("/application1/cta_max_true_batch_dev_20261028")
candidate = base / "batch2_candidate/cta_max"
graph = candidate / "nlp_bert_in_graph.py"
filename = "nlp_encoder.embeddings.word_embeddings.weight.npy"

assert graph.is_file(), "STOP: Batch NLP graph missing"

tree = ast.parse(graph.read_text())
dirname = None

for node in tree.body:
    if isinstance(node, ast.Assign):
        if any(isinstance(t, ast.Name) and t.id == "WEIGHTS"
               for t in node.targets):
            expr = node.value
            if (isinstance(expr, ast.BinOp)
                and isinstance(expr.op, ast.Div)
                and isinstance(expr.right, ast.Constant)
                and isinstance(expr.right.value, str)):
                dirname = expr.right.value

assert dirname and Path(dirname).name == dirname, \
    "STOP: NLP weight-directory definition needs review"

print("EXPECTED NLP DIRECTORY:", dirname)

matches = sorted(
    p for p in (repo / "artifacts/v1.168-max").rglob(filename)
    if p.is_file() and p.parent.name == dirname
)

print("MATCHING NLP EXPORTS:", len(matches))
for p in matches:
    print("FOUND:", p)

assert len(matches) == 1, \
    "STOP: Cannot uniquely identify the existing NLP exports"

source = matches[0].parent
files = sorted(source.glob("*.npy"))

assert files, "STOP: No NLP exports found"

for p in files:
    with p.open("rb") as f:
        assert f.read(6) == b"\x93NUMPY", \
            f"STOP: Invalid NLP weight: {p.name}"

target = candidate / dirname
container_source = (
    "/workspace/" + source.relative_to(repo).as_posix()
)

if target.is_symlink():
    assert os.readlink(target) == container_source, \
        "STOP: Existing NLP link points elsewhere"
    print("NLP WEIGHT LINK: ALREADY CORRECT")
else:
    assert not target.exists(), \
        "STOP: Existing NLP directory must be preserved"
    target.symlink_to(container_source, target_is_directory=True)
    print("NLP WEIGHT LINK: CREATED")

print("NLP WEIGHT FILES VALIDATED:", len(files))
print("CONTAINER SOURCE:", container_source)
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("WORKING HTTP 200: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
