python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
s = p.read_text()
tree = ast.parse(s)

cls = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef) and n.name == "GRecBase"
)

init = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef) and n.name == "__init__"
)

targets = {
    "nlp_encoder", "nlp_dense_0", "nlp_dense_1",
    "nlp_act", "sequence_transformer",
    "task_embedding", "jet_embedding", "ihq_embedding",
    "sibling_context_head", "att_pooling", "mm_pooling",
    "seq_dense", "moe_norm1", "moe_norm2",
    "context_dim", "task_type_dim", "extract_deep_idx"
}

found = set()

print("===== ORIGINAL GRecBase MISSING-LAYER DEFINITIONS =====")

for node in ast.walk(init):
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        continue

    assigned = (
        node.targets if isinstance(node, ast.Assign)
        else [node.target]
    )

    for target in assigned:
        if (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr in targets
        ):
            name = target.attr
            if name not in found:
                found.add(name)
                print("\n###", name)
                print(ast.get_source_segment(s, node))

print("\nNOT DIRECTLY ASSIGNED IN CONSTRUCTOR:")
print(sorted(targets - found))
print("\nREAD-ONLY — NO FILES MODIFIED")
PY
