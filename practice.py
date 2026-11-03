cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

root = Path("artifacts/v1.472-max/pzaas_max")
manifest = json.loads(
    (root/"pzaas_base_weights/manifest.json").read_text()
)

modules = [
    "grecbase_aux_branches_max.py",
    "grecbase_get_path_max.py",
    "main_context_max.py",
    "nlp_bert_in_graph.py",
    "parallel_transformer_block_2layers.py",
    "sibling_context_max.py"
]

for name in modules:
    p = root/name
    print(f"\n=== {name} ===")
    source = p.read_text()
    lines = source.splitlines()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "np"
                    and node.func.attr == "load"):
                    a = max(0, node.lineno-4)
                    b = min(len(lines), node.end_lineno+2)
                    for i in range(a,b):
                        print(f"{i+1}: {lines[i][:160]}")

    for i, line in enumerate(lines,1):
        if line.strip().startswith("def "):
            if any(x in line.lower() for x in
                   ("load", "weight", "norm")):
                print(f"FUNCTION {i}: {line.strip()[:120]}")

print("\n=== AVAILABLE PZAAS WEIGHT PREFIXES ===")
for prefix in (
    "context_head.",
    "sibling_context_head.",
    "sequence_transformer.ptransformer.",
    "nlp_encoder.",
    "att_pooling."
):
    keys = [k for k in manifest if k.startswith(prefix)]
    print(prefix, len(keys), "weights")
    for k in keys[:4]:
        print(" ", k)

print("\nMAPPING ANALYSIS: COMPLETE")
print("NO FILES MODIFIED")
PY
