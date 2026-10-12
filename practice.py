python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

files = {
    "runner": base / "run_transformer_full_sequence.py",
    "graph": base / "parallel_transformer_graph_full_sequence.py",
    "features": base / "sequence_transformer_max.py",
}

for name, path in files.items():
    assert path.is_file(), f"STOP: missing {name}: {path}"

def load(path):
    s = path.read_text()
    return s, ast.parse(s)

runner_source, runner = load(files["runner"])
graph_source, graph = load(files["graph"])
feature_source, features = load(files["features"])

print("===== RUNNER: ACTUAL GRAPH IMPORTS =====")
for node in ast.walk(runner):
    if isinstance(node, ast.ImportFrom):
        if "graph" in (node.module or ""):
            print(ast.get_source_segment(runner_source, node))

print("\n===== RUNNER: GRAPH BUILDER CALLS =====")
for node in ast.walk(runner):
    if isinstance(node, ast.Call):
        fn = node.func
        name = fn.id if isinstance(fn, ast.Name) else (
            fn.attr if isinstance(fn, ast.Attribute) else ""
        )
        if "build_parallel_transformer_graph" in name:
            print(ast.get_source_segment(runner_source, node))

print("\n===== FEATURE MODULE RETURN =====")
cls = next(
    n for n in features.body
    if isinstance(n, ast.ClassDef)
    and n.name == "ParallelTransformerMAEPMAX"
)
method = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "__call__"
)
for node in ast.walk(method):
    if isinstance(node, ast.Return):
        print(ast.get_source_segment(feature_source, node))

print("\n===== FULL GRAPH: FEATURE ASSEMBLY =====")
builder = next(
    n for n in graph.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "build_parallel_transformer_graph"
)
for node in ast.walk(builder):
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        segment = ast.get_source_segment(graph_source, node)
        if any(x in segment for x in (
            "features(", "block0(", "block1(", "postprocess("
        )):
            print(segment)

print("\nINTEGRATION CONNECTION CHECK COMPLETE")
print("NO FILES MODIFIED")
PY
