python - <<'PY'
import ast
from pathlib import Path

files = [
    ("ORIGINAL", Path("artifacts/v1.168/utils/dependency-utils/models.py"), "ParallelTransformerAEP"),
    ("MAX", Path("artifacts/v1.168-max/cta_max/sequence_transformer_max.py"), "ParallelTransformerMAEPMAX"),
]

for label, path, name in files:
    source = path.read_text()
    tree = ast.parse(source)
    classes = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef) and n.name == name
    ]
    assert len(classes) == 1, f"STOP: {name} not uniquely found"

    init = next(
        n for n in classes[0].body
        if isinstance(n, ast.FunctionDef) and n.name == "__init__"
    )

    print(f"\n===== {label} CONSTRUCTOR =====")
    for node in init.body:
        line = ast.get_source_segment(source, node)
        if line and any(k in line for k in [
            "page_meta_wide", "item_meta_wide",
            "embedding", "num_layers", "ptransformer",
            "out_norm", "seq_pooling", "seq_dense"
        ]):
            print(line[:1200])
PY
