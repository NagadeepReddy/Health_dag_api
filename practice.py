cd /application1/sajjna8/rt-pzaas-v1.0 && \
M="$PWD/artifacts/v1.472-max" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
-e PYTHONDONTWRITEBYTECODE=1 \
-v "$M:/models:ro" \
-w /models \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
from pathlib import Path
import ast
import numpy as np

root = Path("/models/pzaas_max")

print("=== PZAAS FINAL TWO BRANCHES ===")

target = root / "validation/pzaas_eight_branch_targets.npz"

with np.load(target, allow_pickle=False) as data:
    print("\nPYTORCH BRANCH TARGETS:")
    for key in data.files:
        print(key, data[key].shape)

for name in [
    "main_context_max.py",
    "parallel_transformer_block_2layers.py",
    "grecbase_fusion_full_head_72_max.py"
]:
    p = root / name
    print("\nFILE:", name)

    if not p.is_file():
        print("NOT FOUND")
        continue

    source = p.read_text()
    tree = ast.parse(source)
    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if any(x in node.name.lower() for x in [
                "context", "sequence", "fusion",
                "transformer", "features"
            ]):
                print(
                    "FUNCTION:", node.name,
                    "LINES:", node.lineno, "-", node.end_lineno
                )

    if name == "grecbase_fusion_full_head_72_max.py":
        print("\nSEQUENCE / CONTEXT WIRING:")
        for i, line in enumerate(lines, 1):
            if any(x in line for x in [
                "main_context_forward",
                "ParallelTransformer",
                "features(",
                "postprocess(",
                "seq_dense",
                "context_inputs",
                "graph.output"
            ]):
                print(f"{i}: {line.strip()}")

print("\nFINAL BRANCH INSPECTION: COMPLETE")
print("ORIGINAL DS: UNCHANGED")
print("NEXT: SEQUENCE + CONTEXT REAL MAX PARITY")
PY
