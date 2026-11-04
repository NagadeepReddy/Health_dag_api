cd /application1/sajjna8/rt-pzaas-v1.0 && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --network none \
-v /application1:/application1:ro \
-w /application1/sajjna8/rt-pzaas-v1.0 \
-e PYTHONPATH=/application1/sajjna8/rt-pzaas-v1.0/artifacts/v1.472-max \
--entrypoint /bin/sh \
localhost/cta-max-faiss:local -c 'exec python3 -' <<'PY'
import inspect
import ast
import textwrap
from pathlib import Path
from pzaas_max.grecbase_fusion_full_head_72_max import (
    build_grecbase_fusion_graph_order_correct
)

print("=== PZAAS EXACT 72-INPUT SOURCE MAPPING ===")

src = textwrap.dedent(
    inspect.getsource(build_grecbase_fusion_graph_order_correct)
)

for n, line in enumerate(src.splitlines(), 1):
    if any(k in line for k in (
        "remaining[", "graph.inputs", "input_types",
        "deep =", "wide =", "sibling",
        "sequence", "search", "context",
        "input_ids", "attention_mask"
    )):
        print(f"{n}: {line.strip()}")

print("\n=== ORDERED INPUT ASSIGNMENTS ===")
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        statement = ast.unparse(node)
        if "remaining[" in statement or "graph.inputs" in statement:
            print(statement[:500])

print("\n=== DERIVED SEQUENCE INPUT LOCATIONS ===")
root = Path("artifacts/v1.472-max/pzaas_max")
for path in sorted(root.glob("*.py")):
    lines = path.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines, 1):
        if any(k in line for k in (
            "50, 256", "50,256",
            "remaining[29]", "remaining[28]",
            "ppa_tensor_inputs"
        )):
            print(f"{path.name}:{i}: {line.strip()[:200]}")

print("\nORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: EXACT INPUT PACKING → FULL NUMERICAL PARITY")
PY
