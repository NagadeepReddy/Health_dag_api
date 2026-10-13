python - <<'PY'
from pathlib import Path
import ast
import re

base = Path("artifacts/v1.168-max/cta_max")

graph_src = base / "grecbase_fusion_order_correct_max.py"
runner_src = base / "run_real_sanity_max_full.py"

graph_diag = base / "grecbase_fusion_order_correct_max_branch_diag.py"
runner_diag = base / "run_real_sanity_max_branch_diag.py"

source = graph_src.read_text()

pattern = r'(?m)^([ \t]*)graph\.output\(\s*result\s*\)\s*$'
matches = list(re.finditer(pattern, source))

if len(matches) != 1:
    raise SystemExit(
        "STOP: Expected single final graph.output(result) not found"
    )

names = [
    "seq", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]

for name in names:
    if not re.search(r'\b' + name + r'\b', source):
        raise SystemExit(f"STOP: Missing branch variable: {name}")

updated_graph = re.sub(
    pattern,
    lambda m: (
        m.group(1)
        + "graph.output(result, " + ", ".join(names) + ")"
    ),
    source,
    count=1
)

ast.parse(updated_graph)

runner = runner_src.read_text()

old_import = "from cta_max.grecbase_fusion_order_correct_max import ("
new_import = (
    "from cta_max.grecbase_fusion_order_correct_max_branch_diag import ("
)

if runner.count(old_import) != 1:
    raise SystemExit("STOP: Expected working graph import not found")

runner = runner.replace(old_import, new_import, 1)

anchor = "outputs = model.execute(*runtime_inputs)"

diagnostic = '''
print("\\n=== CURRENT REAL-INPUT EIGHT-BRANCH PARITY ===", flush=True)

branches = [
    "seq_PLACEHOLDER", "context", "search0", "search1",
    "task", "jet", "ihq", "sibling"
]
branches[0] = "sequence"

if len(outputs) != 9:
    raise RuntimeError(
        f"Expected main output + 8 branches, received {len(outputs)}"
    )

reference_file = BASE / "real_sanity_pytorch_branches.npz"

with np.load(reference_file, allow_pickle=False) as references:
    passed = 0

    for index, name in enumerate(branches, start=1):
        if name not in references:
            print(name, "REFERENCE MISSING")
            continue

        expected = np.asarray(references[name], dtype=np.float32)
        actual = np.asarray(
            outputs[index].to_numpy(), dtype=np.float32
        )

        if actual.size != expected.size:
            print(
                name, "SIZE MISMATCH",
                "PT:", expected.shape,
                "MAX:", actual.shape
            )
            continue

        actual = actual.reshape(expected.shape)

        difference = np.abs(
            actual.astype(np.float64)
            - expected.astype(np.float64)
        )

        match = bool(np.allclose(
            actual, expected,
            rtol=1e-3, atol=1e-3
        ))

        passed += int(match)

        print(
            name,
            "PASS" if match else "FAIL",
            "MAX_DIFF:", float(difference.max()),
            "MEAN_DIFF:", float(difference.mean())
        )

    print("\\nCURRENT BRANCH PARITY:", passed, "/8")
'''

if runner.count(anchor) != 1:
    raise SystemExit("STOP: Expected execution line not found")

runner = runner.replace(anchor, anchor + "\n" + diagnostic, 1)
ast.parse(runner)

for path, content in [
    (graph_diag, updated_graph),
    (runner_diag, runner),
]:
    if path.exists():
        if path.read_text() != content:
            raise SystemExit(
                f"STOP: Existing diagnostic file differs: {path}"
            )

for path, content in [
    (graph_diag, updated_graph),
    (runner_diag, runner),
]:
    if not path.exists():
        path.write_text(content)
        print("CREATED:", path)
    else:
        print("REUSING:", path)

print("WORKING SOURCE AND TRAINED WEIGHTS UNCHANGED")
PY

podman run --rm -i \
  -v "$PWD:/workspace" \
  -w /workspace \
  --entrypoint python \
  docker-remote.oneartifactoryci.verizon.com/modular/max-full:latest \
  artifacts/v1.168-max/cta_max/run_real_sanity_max_branch_diag.py
