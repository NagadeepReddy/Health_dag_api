python - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")

source_graph = base / "grecbase_fusion_order_correct_max_branch_diag.py"
source_runner = base / "run_real_sanity_max_branch_diag.py"

trial_graph = base / "grecbase_fusion_order_correct_max_seqbias_trial.py"
trial_runner = base / "run_real_sanity_max_seqbias_trial.py"

source = source_graph.read_text()
tree = ast.parse(source)

matches = [
    n for n in ast.walk(tree)
    if isinstance(n, (ast.Assign, ast.AnnAssign))
    and any(
        isinstance(t, ast.Name) and t.id == "seq_b"
        for t in (
            n.targets if isinstance(n, ast.Assign)
            else [n.target]
        )
    )
]

if len(matches) != 1:
    raise SystemExit(
        f"STOP: Expected one seq_b assignment, found {len(matches)}"
    )

node = matches[0]
lines = source.splitlines(keepends=True)

start = sum(len(line) for line in lines[:node.lineno - 1]) + node.col_offset
end = sum(len(line) for line in lines[:node.end_lineno - 1]) + node.end_col_offset

replacement = (
    'seq_b = np.load(WDIR / "seq_dense.bias.npy")'
    '.astype(np.float32)'
)

updated_graph = source[:start] + replacement + source[end:]
ast.parse(updated_graph)

runner = source_runner.read_text()

old_import = "cta_max.grecbase_fusion_order_correct_max_branch_diag"
new_import = "cta_max.grecbase_fusion_order_correct_max_seqbias_trial"

if runner.count(old_import) != 1:
    raise SystemExit("STOP: Existing diagnostic graph import not found")

updated_runner = runner.replace(old_import, new_import, 1)
ast.parse(updated_runner)

for path, content in [
    (trial_graph, updated_graph),
    (trial_runner, updated_runner),
]:
    if path.exists() and path.read_text() != content:
        raise SystemExit(f"STOP: Trial file already differs: {path}")

for path, content in [
    (trial_graph, updated_graph),
    (trial_runner, updated_runner),
]:
    if not path.exists():
        path.write_text(content)
    print("READY:", path.name)

print("WORKING MODEL, PYTORCH, DS AND WEIGHTS UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_seqbias_trial.py
