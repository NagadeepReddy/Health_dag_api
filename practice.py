cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import os

repo = Path.cwd()
base = Path("/application1/cta_max_true_batch_dev_20261028")
candidate = base / "batch2_candidate/cta_max"
graph = candidate / "nlp_bert_in_graph.py"
filename = "nlp_encoder.embeddings.word_embeddings.weight.npy"

assert graph.is_file(), "STOP: NLP graph missing"

source_code = graph.read_text()
tree = ast.parse(source_code)

assignments = [
    n for n in tree.body
    if isinstance(n, (ast.Assign, ast.AnnAssign))
    and any(
        isinstance(t, ast.Name) and t.id == "WEIGHTS"
        for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
    )
]

assert len(assignments) == 1, "STOP: WEIGHTS assignment ambiguous"

expr = ast.get_source_segment(source_code, assignments[0].value)
print("ACTUAL WEIGHTS DEFINITION:", expr)

def path_parts(node):
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        if isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            return path_parts(node.left) + [node.right.value]
    return []

parts = path_parts(assignments[0].value)

assert "__file__" in expr and ".parent" in expr and parts, \
    "STOP: Cannot safely resolve NLP weight location"

assert all(
    p and not Path(p).is_absolute() and ".." not in Path(p).parts
    for p in parts
), "STOP: Unsafe directory definition"

target = candidate.joinpath(*parts)

roots = [
    repo / "artifacts/v1.168-max",
    base / "cta_max",
]

matches = []
for root in roots:
    if root.is_dir():
        matches.extend(
            p for p in root.rglob(filename)
            if p.is_file()
        )

sources = sorted(set(p.parent.resolve() for p in matches))
print("NLP WEIGHT DIRECTORIES FOUND:", len(sources))

for p in sources:
    print("SOURCE:", p)

assert len(sources) == 1, \
    "STOP: Source missing or ambiguous; preserve existing files"

source = sources[0]
weights = sorted(source.glob("*.npy"))

for p in weights:
    with p.open("rb") as f:
        assert f.read(6) == b"\x93NUMPY", \
            f"STOP: Invalid NPY file {p.name}"

assert weights, "STOP: No exported NLP weights"

# The original repository is mounted at /workspace in the test container.
assert source.is_relative_to(repo), \
    "STOP: Source is not available under the container's /workspace mount"

container_source = "/workspace/" + source.relative_to(repo).as_posix()

assert target.parent.is_dir(), "STOP: Candidate parent directory missing"

if target.is_symlink():
    assert os.readlink(target) == container_source, \
        "STOP: Existing link differs"
    print("NLP LINK: ALREADY CORRECT")
elif target.exists():
    print("STOP: Existing directory preserved; manual reconciliation needed")
    raise SystemExit(1)
else:
    target.symlink_to(container_source, target_is_directory=True)
    print("NLP LINK: CREATED")

print("NLP EXPORTED WEIGHTS:", len(weights))
print("NLP WEIGHT SOURCE: VERIFIED")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
