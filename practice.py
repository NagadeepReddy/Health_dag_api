python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
tree = ast.parse(p.read_text())

cls = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef)
    and n.name == "GRecBase"
)

forward = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef)
    and n.name == "forward"
)

targets = {
    "nlp_encoder",
    "nlp_dense_0",
    "nlp_dense_1",
    "sequence_transformer",
    "context_head",
    "sibling_context_head",
    "att_pooling",
}

class Trace(ast.NodeVisitor):
    def __init__(self):
        self.conditions = []

    def visit_If(self, node):
        condition = ast.unparse(node.test)
        self.conditions.append(condition)
        for child in node.body:
            self.visit(child)
        self.conditions.pop()

        self.conditions.append("ELSE of: " + condition)
        for child in node.orelse:
            self.visit(child)
        self.conditions.pop()

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
            and node.func.attr in targets
        ):
            print("\nCALL:", node.func.attr)
            print("LINE:", node.lineno)
            print("CONDITIONS:", self.conditions or ["UNCONDITIONAL"])
            print("ARGUMENTS:", [
                ast.unparse(a) for a in node.args
            ])
        self.generic_visit(node)

print("===== ACTUAL GRecBase EXECUTION BRANCHES =====")
Trace().visit(forward)
print("\nREAD-ONLY — NO FILES MODIFIED")
PY
