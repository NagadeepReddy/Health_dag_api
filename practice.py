python - <<'PY'
from pathlib import Path
import ast
import re

base = Path("artifacts/v1.168-max/cta_max")
src_graph = base / "grecbase_fusion_order_correct_max_branch_diag.py"
src_runner = base / "run_real_sanity_max_branch_diag.py"
trial_graph = base / "grecbase_fusion_seq_isolation_trial.py"
trial_runner = base / "run_real_sanity_seq_isolation_trial.py"
ref = base / "real_sanity_pytorch_same_input_verified.npz"

for p in (src_graph, src_runner, ref):
    if not p.is_file():
        raise SystemExit(f"STOP: Missing verified file: {p}")

source = src_graph.read_text()
tree = ast.parse(source)

assignments = [
    node for node in ast.walk(tree)
    if isinstance(node, ast.Assign)
    and any(
        isinstance(t, ast.Name) and t.id == "seq"
        for t in node.targets
    )
]

if len(assignments) != 1:
    raise SystemExit(
        f"STOP: Expected one sequence assignment; found {len(assignments)}. "
        "No files changed."
    )

node = assignments[0]
lines = source.splitlines(keepends=True)
indent = re.match(r"[ \t]*", lines[node.lineno - 1]).group()

addition = (
    indent + "# DIAGNOSTIC ONLY: substitute verified PyTorch sequence\n"
    + indent + "seq = ops.constant(\n"
    + indent + '    np.load('
      '"artifacts/v1.168-max/cta_max/'
      'real_sanity_pytorch_same_input_verified.npz", '
      'allow_pickle=False)["sequence"].astype(np.float32),\n'
    + indent + "    dtype=DType.float32, device=device\n"
    + indent + ")\n"
)

lines.insert(node.end_lineno, addition)
updated_graph = "".join(lines)
ast.parse(updated_graph)

runner = src_runner.read_text()
old_import = "cta_max.grecbase_fusion_order_correct_max_branch_diag"
new_import = "cta_max.grecbase_fusion_seq_isolation_trial"

if runner.count(old_import) != 1:
    raise SystemExit("STOP: Diagnostic graph import not uniquely found")

updated_runner = runner.replace(old_import, new_import, 1)
ast.parse(updated_runner)

for p, content in (
    (trial_graph, updated_graph),
    (trial_runner, updated_runner),
):
    if p.exists() and p.read_text() != content:
        raise SystemExit(f"STOP: Existing trial differs: {p}")

for p, content in (
    (trial_graph, updated_graph),
    (trial_runner, updated_runner),
):
    if not p.exists():
        p.write_text(content)
    print("TRIAL READY:", p.name)

print("DIAGNOSTIC ONLY — NOT A PRODUCTION MAX FIX")
print("ORIGINAL MAX, PYTORCH, DS AND WEIGHTS UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_seq_isolation_trial.py
